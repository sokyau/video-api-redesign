# src/worker.py
import sys
import os
import time
import logging
import signal
# Corregido
from .services.queue_service import process_queue
from .services.cleanup_service import cleanup_service
from .config import settings

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(settings.LOG_DIR, 'worker.log'))
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

def main():
    """Función principal del worker"""
    logger.info("Iniciando worker de procesamiento...")
    
    # Iniciar servicio de limpieza
    cleanup_service.start()
    logger.info("Servicio de limpieza iniciado")
    
    # Bucle principal de procesamiento
    while running:
        try:
            # Procesar tareas pendientes en la cola
            tasks_processed = process_queue(max_tasks=10)
            
            if tasks_processed:
                logger.info(f"Procesadas {tasks_processed} tareas")
            
            # Esperar un poco antes de verificar de nuevo
            time.sleep(1)
            
        except Exception as e:
            logger.exception(f"Error en bucle de worker: {str(e)}")
            time.sleep(5)  # Esperar más tiempo en caso de error
    
    # Limpieza al salir
    cleanup_service.stop()
    logger.info("Worker terminado correctamente")

if __name__ == "__main__":
    main()
