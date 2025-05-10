# src/services/__init__.py

# Importar servicios principales
from .video_service import add_captions_to_video, process_meme_overlay, concatenate_videos_service
from .media_service import extract_audio, transcribe_media
from .ffmpeg_service import run_ffmpeg_command, get_media_info, compose_ffmpeg
from .storage_service import store_file, get_file_url, cleanup_old_files, ensure_storage_dir
from .animation_service import animated_text_service, build_animation_filter
from .webhook_service import send_webhook, notify_job_completed, notify_job_failed
from .cleanup_service import cleanup_service

# Exponer el servicio de cola
from .queue_service import (
    enqueue_task, 
    get_task_status, 
    queue_task_wrapper, 
    process_queue,
    TaskStatus
)

# Opcional: Redis Queue Service si está disponible
try:
    from .redis_queue_service import (
        redis_client,
        enqueue_task as redis_enqueue_task,
        get_task_status as redis_get_task_status,
        update_task_status,
        fetch_pending_task,
        get_queue_stats
    )
except ImportError:
    # Redis queue service no está disponible, ignorar silenciosamente
    pass

# Definir variables expuestas explícitamente para mejor documentación
__all__ = [
    # Video services
    'add_captions_to_video', 'process_meme_overlay', 'concatenate_videos_service',
    # Media services
    'extract_audio', 'transcribe_media',
    # FFmpeg services
    'run_ffmpeg_command', 'get_media_info', 'compose_ffmpeg',
    # Storage services
    'store_file', 'get_file_url', 'cleanup_old_files', 'ensure_storage_dir',
    # Animation services
    'animated_text_service', 'build_animation_filter',
    # Webhook services
    'send_webhook', 'notify_job_completed', 'notify_job_failed',
    # Cleanup service
    'cleanup_service',
    # Queue services
    'enqueue_task', 'get_task_status', 'queue_task_wrapper', 'process_queue', 'TaskStatus'
]
