import json
import logging
import time
import uuid
import redis
from typing import Dict, Any, Callable, Optional
from redis.exceptions import RedisError
from ..config import settings

logger = logging.getLogger(__name__)

try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        socket_connect_timeout=5,
        socket_timeout=5,
        decode_responses=True
    )
    redis_client.ping()
    logger.info(f"Conectado a Redis: {settings.REDIS_URL}")
except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
    logger.error(f"Error conectando a Redis: {str(e)}")
    redis_client = None

QUEUE_NAME = "video_api:queue"
TASK_INFO_PREFIX = "video_api:task:"

class TaskStatus:
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

def generate_job_id() -> str:
    return str(uuid.uuid4())

def enqueue_task(task_func_name: str, job_id: str = None, **kwargs) -> Dict[str, Any]:
    if not redis_client:
        raise RuntimeError("Redis no disponible para encolado de tareas")
    
    if not job_id:
        job_id = generate_job_id()
    
    task_data = {
        "job_id": job_id,
        "status": TaskStatus.QUEUED,
        "created_at": time.time(),
        "task_func": task_func_name,
        "kwargs": kwargs,
        "updated_at": time.time()
    }
    
    task_key = f"{TASK_INFO_PREFIX}{job_id}"
    redis_client.set(task_key, json.dumps(task_data))
    
    redis_client.lpush(QUEUE_NAME, json.dumps({
        "job_id": job_id,
        "task_func": task_func_name,
        "kwargs": kwargs
    }))
    
    logger.info(f"Tarea encolada en Redis: {job_id}")
    
    return {
        "job_id": job_id,
        "status": TaskStatus.QUEUED,
        "created_at": task_data["created_at"]
    }

def get_task_status(job_id: str) -> Optional[Dict[str, Any]]:
    if not redis_client:
        raise RuntimeError("Redis no disponible para consultar estado")
    
    task_key = f"{TASK_INFO_PREFIX}{job_id}"
    task_data = redis_client.get(task_key)
    
    if not task_data:
        return None
    
    return json.loads(task_data)

def update_task_status(job_id: str, status: str, result=None, error=None) -> bool:
    if not redis_client:
        raise RuntimeError("Redis no disponible para actualizar estado")
    
    task_key = f"{TASK_INFO_PREFIX}{job_id}"
    task_data_str = redis_client.get(task_key)
    
    if not task_data_str:
        logger.warning(f"Intento de actualizar tarea inexistente: {job_id}")
        return False
    
    task_data = json.loads(task_data_str)
    task_data["status"] = status
    task_data["updated_at"] = time.time()
    
    if status == TaskStatus.COMPLETED:
        task_data["result"] = result
        task_data["completed_at"] = time.time()
    elif status == TaskStatus.FAILED:
        task_data["error"] = error
    
    redis_client.set(task_key, json.dumps(task_data))
    logger.debug(f"Actualizado estado de tarea {job_id} a {status}")
    
    return True

def fetch_pending_task() -> Optional[Dict[str, Any]]:
    if not redis_client:
        raise RuntimeError("Redis no disponible para obtener tareas")
    
    task_data = redis_client.rpop(QUEUE_NAME)
    
    if not task_data:
        return None
    
    return json.loads(task_data)

task_functions_registry = {}

def register_task_functions(task_functions: Dict[str, Callable]) -> None:
    global task_functions_registry
    task_functions_registry = task_functions
    logger.info(f"Registradas {len(task_functions)} funciones de tarea")

def get_queue_stats() -> Dict[str, Any]:
    if not redis_client:
        raise RuntimeError("Redis no disponible para estadísticas")
    
    queue_length = redis_client.llen(QUEUE_NAME)
    
    task_keys = redis_client.keys(f"{TASK_INFO_PREFIX}*")
    status_counts = {
        TaskStatus.QUEUED: 0,
        TaskStatus.PROCESSING: 0,
        TaskStatus.COMPLETED: 0,
        TaskStatus.FAILED: 0
    }
    
    for key in task_keys:
        task_data_str = redis_client.get(key)
        if task_data_str:
            task_data = json.loads(task_data_str)
            status = task_data.get("status")
            if status in status_counts:
                status_counts[status] += 1
    
    return {
        "queue_length": queue_length,
        "total_tasks": len(task_keys),
        "tasks_by_status": status_counts
    }
