
# src/services/queue_service.py
import logging
import time
import uuid
import json
import threading
from typing import Dict, Any, Callable, Optional
from queue import Queue, Empty
from src.config import settings

logger = logging.getLogger(__name__)

# Cola de tareas
task_queue = Queue(maxsize=settings.MAX_QUEUE_LENGTH)

# Almacenamiento de tareas
tasks = {}  # job_id -> task_info

# Workers
workers = []

class TaskStatus:
    """Estados de tareas"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

def generate_job_id() -> str:
    """Genera un ID único para trabajo"""
    return str(uuid.uuid4())

def enqueue_task(task_func: Callable, job_id: str = None, **kwargs) -> Dict[str, Any]:
    """
    Añade una tarea a la cola de procesamiento
    
    Args:
        task_func: Función a ejecutar
        job_id: ID de trabajo opcional (se genera si no se proporciona)
        **kwargs: Argumentos para la función
    
    Returns:
        dict: Información de la tarea, incluyendo job_id
    """
    if task_queue.qsize() >= settings.MAX_QUEUE_LENGTH:
        raise RuntimeError("Cola de tareas llena")
    
    if not job_id:
        job_id = generate_job_id()
    
    task_info = {
        "job_id": job_id,
        "status": TaskStatus.QUEUED,
        "created_at": time.time(),
        "kwargs": kwargs,
        "updated_at": time.time(),
        "result": None,
        "error": None
    }
    
    # Almacenar información de tarea
    tasks[job_id] = task_info
    
    # Añadir a la cola
    task_queue.put({
        "job_id": job_id,
        "task_func": task_func,
        "kwargs": kwargs
    })
    
    logger.info(f"Tarea encolada: {job_id}")
    return task_info

def get_task_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene el estado de una tarea
    
    Args:
        job_id: ID del trabajo a consultar
    
    Returns:
        dict: Información de la tarea o None si no se encuentra
    """
    return tasks.get(job_id)

def worker_thread():
    """Hilo trabajador para procesar tareas de la cola"""
    logger.info(f"Iniciando hilo trabajador: {threading.current_thread().name}")
    
    while True:
        try:
            # Obtener tarea de la cola
            task = task_queue.get(timeout=1)
            
            job_id = task["job_id"]
            task_func = task["task_func"]
            kwargs = task["kwargs"]
            
            # Actualizar estado
            tasks[job_id]["status"] = TaskStatus.PROCESSING
            tasks[job_id]["updated_at"] = time.time()
            
            logger.info(f"Procesando tarea {job_id}")
            
            try:
                # Ejecutar función de tarea
                result = task_func(**kwargs)
                
                # Actualizar con éxito
                tasks[job_id]["status"] = TaskStatus.COMPLETED
                tasks[job_id]["result"] = result
                tasks[job_id]["updated_at"] = time.time()
                tasks[job_id]["completed_at"] = time.time()
                
                logger.info(f"Tarea {job_id} completada exitosamente")
                
            except Exception as e:
                # Actualizar con fallo
                tasks[job_id]["status"] = TaskStatus.FAILED
                tasks[job_id]["error"] = str(e)
                tasks[job_id]["updated_at"] = time.time()
                
                logger.exception(f"Tarea {job_id} falló: {str(e)}")
            
            # Marcar tarea como completada en la cola
            task_queue.task_done()
            
        except Empty:
            # Cola vacía, continuar
            pass
        except Exception as e:
            logger.exception(f"Error en hilo trabajador: {str(e)}")

def start_workers(num_workers: int = None):
    """
    Inicia hilos trabajadores
    
    Args:
        num_workers: Número de hilos trabajadores (por defecto de settings)
    """
    if not num_workers:
        num_workers = settings.WORKER_PROCESSES
    
    for i in range(num_workers):
        worker = threading.Thread(
            target=worker_thread,
            name=f"Worker-{i+1}",
            daemon=True
        )
        worker.start()
        workers.append(worker)
    
    logger.info(f"Iniciados {num_workers} hilos trabajadores")

def queue_task_wrapper(bypass_queue: bool = False):
    """
    Decorador para gestionar encolado de tareas
    
    Args:
        bypass_queue: Si es True, ejecuta inmediatamente
    """
    def decorator(f):
        def wrapped_function(*args, **kwargs):
            # Extraer job_id de kwargs si está presente
            job_id = kwargs.get('job_id')
            
            # Ejecutar inmediatamente si se bypasea la cola
            if bypass_queue:
                logger.debug(f"Bypassing cola para job {job_id}")
                return f(*args, **kwargs)
            
            # De lo contrario, encolar tarea
            task_info = enqueue_task(f, job_id=job_id, **kwargs)
            
            return task_info
        return wrapped_function
    return decorator
# Añadir a src/services/queue_service.py

def process_queue(max_tasks=None):
    """
    Procesa tareas pendientes en la cola
    
    Args:
        max_tasks: Número máximo de tareas a procesar (None = sin límite)
    
    Returns:
        int: Número de tareas procesadas
    """
    tasks_processed = 0
    
    while True:
        # Verificar límite de tareas
        if max_tasks is not None and tasks_processed >= max_tasks:
            break
        
        try:
            # Intentar obtener tarea (no bloqueante)
            task = task_queue.get_nowait()
            
            job_id = task["job_id"]
            task_func = task["task_func"]
            kwargs = task["kwargs"]
            
            # Actualizar estado
            tasks[job_id]["status"] = TaskStatus.PROCESSING
            tasks[job_id]["updated_at"] = time.time()
            
            logger.info(f"Procesando tarea {job_id}")
            
            try:
                # Ejecutar función de tarea
                result = task_func(**kwargs)
                
                # Actualizar con éxito
                tasks[job_id]["status"] = TaskStatus.COMPLETED
                tasks[job_id]["result"] = result
                tasks[job_id]["updated_at"] = time.time()
                tasks[job_id]["completed_at"] = time.time()
                
                logger.info(f"Tarea {job_id} completada exitosamente")
                
            except Exception as e:
                # Actualizar con fallo
                tasks[job_id]["status"] = TaskStatus.FAILED
                tasks[job_id]["error"] = str(e)
                tasks[job_id]["updated_at"] = time.time()
                
                logger.exception(f"Tarea {job_id} falló: {str(e)}")
            
            # Marcar tarea como completada en la cola
            task_queue.task_done()
            
            # Incrementar contador
            tasks_processed += 1
            
        except Empty:
            # Cola vacía, salir del bucle
            break
        except Exception as e:
            logger.exception(f"Error procesando tarea: {str(e)}")
            # Continuar con la siguiente tarea
    
    return tasks_processed

# Inicializar workers al importar el módulo
start_workers()
