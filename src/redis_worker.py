# src/redis_worker.py
import sys
import os
import time
import logging
import signal
import importlib
from src.services.redis_queue_service import fetch_pending_task, update_task_status, TaskStatus
from src.services.cleanup_service import cleanup_service
from src.config import settings

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(settings.LOG_DIR, 'redis_worker.log'))
    ]
)

logger = logging.getLogger(__name__)

# Flags para manejo de señales
running = True

def signal_handler(sig, frame):
    """Manejador de señales para salir limpiamente"""
    global running
    logger.info(f"Recibida señal {sig}, terminando...")
    running = False

# Registrar manejadores de señales
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Diccionario de funciones disponibles
task_functions = {}

def load_task_functions():
    """
    Carga dinámicamente las funciones de tarea
    """
    # Importar y registrar funciones de servicios
    from src.services.video_service import add_captions_to_video, process_meme_overlay
    from src.services.media_service import extract_audio, transcribe_media
    
    # Registrar cada función con su nombre
    task_functions.update({
        'add_captions_to_video': add_captions_to_video,
        'process_meme_overlay': process_meme_overlay,
        'extract_audio': extract_audio,
        'transcribe_media': transcribe_media
    })
    
    logger.info(f"Cargadas {len(task_functions)} funciones de tarea")

def main():
    """Función principal del worker de Redis"""
    logger.info("Iniciando worker de Redis...")
    
    # Cargar funciones disponibles
    load_task_functions()
    
    # Iniciar servicio de limpieza
    cleanup_service.start()
    logger.info("Servicio de limpieza iniciado")
    
    # Tiempo entre comprobaciones de cola si está vacía
    poll_interval = 1
    
    # Bucle principal de procesamiento
    while running:
        try:
            # Obtener tarea pendiente
            task = fetch_pending_task()
            
            if task:
                job_id = task.get("job_id")
                task_func_name = task.get("task_func")
                kwargs = task.get("kwargs", {})
                
                logger.info(f"Procesando tarea {job_id}: {task_func_name}")
                
                # Actualizar estado
                update_task_status(job_id, TaskStatus.PROCESSING)
                
                try:
                    # Verificar que la función existe
                    if task_func_name not in task_functions:
                        raise ValueError(f"Función desconocida: {task_func_name}")
                    
                    # Ejecutar función
                    task_func = task_functions[task_func_name]
                    result = task_func(**kwargs)
                    
                    # Actualizar resultado
                    update_task_status(job_id, TaskStatus.COMPLETED, result=result)
                    logger.info(f"Tarea {job_id} completada exitosamente")
                    
                except Exception as e:
                    # Actualizar error
                    logger.exception(f"Error ejecutando tarea {job_id}: {str(e)}")
                    update_task_status(job_id, TaskStatus.FAILED, error=str(e))
            else:
                # No hay tareas, esperar
                time.sleep(poll_interval)
                
        except Exception as e:
            logger.exception(f"Error en bucle de worker: {str(e)}")
            time.sleep(5)  # Esperar más tiempo en caso de error
    
    # Limpieza al salir
    cleanup_service.stop()
    logger.info("Worker de Redis terminado correctamente")

if __name__ == "__main__":
    main()

