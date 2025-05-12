import os
import logging
import time
import uuid
from ..utils.file_utils import download_file, generate_temp_filename, verify_file_integrity
from ..services.ffmpeg_service import run_ffmpeg_command, get_media_info
from ..services.storage_service import store_file
from ..services.webhook_service import notify_job_completed, notify_job_failed
from ..config import settings
from ..api.middlewares.error_handler import ProcessingError

logger = logging.getLogger(__name__)

def extract_audio(media_url: str, bitrate: str = '192k', format: str = 'mp3', job_id: str = None, webhook_url: str = None) -> str:
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando extracción de audio desde {media_url}")
    
    media_path = None
    output_path = None
    
    try:
        media_path = download_file(media_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Archivo multimedia descargado: {media_path}")
        
        media_info = get_media_info(media_path)
        logger.debug(f"Job {job_id}: Información multimedia: {media_info}")
        
        output_path = generate_temp_filename(prefix=f"{job_id}_audio_", suffix=f".{format}")
        
        command = [
            'ffmpeg',
            '-i', media_path,
            '-vn',
            '-b:a', bitrate
        ]
        
        if format == 'mp3':
            command.extend(['-codec:a', 'libmp3lame', '-q:a', '2'])
        elif format == 'wav':
            command.extend(['-codec:a', 'pcm_s16le'])
        elif format == 'aac':
            command.extend(['-codec:a', 'aac']) 
        elif format == 'flac':
            command.extend(['-codec:a', 'flac'])
        
        command.append(output_path)
        
        run_ffmpeg_command(command)
        
        if not verify_file_integrity(output_path):
            logger.error(f"Job {job_id}: El archivo de audio extraído no es válido o no se creó: {output_path}")
            raise ProcessingError("El archivo de audio extraído no es válido")
        
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Audio extraído y almacenado: {result_url}")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error extrayendo audio: {str(e)}")
        
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        raise
        
    finally:
        for file_path in [media_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Error eliminando archivo temporal {file_path}: {str(e)}")

def transcribe_media(media_url: str, language: str = 'auto', output_format: str = 'txt', job_id: str = None, webhook_url: str = None) -> dict:
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando transcripción desde {media_url}")
    
    media_path = None
    audio_path = None
    
    try:
        media_path = download_file(media_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Archivo multimedia descargado: {media_path}")
        
        audio_path = generate_temp_filename(prefix=f"{job_id}_audio_transcribe_", suffix=".wav")
        
        command = [
            'ffmpeg',
            '-i', media_path,
            '-vn',
            '-ar', '16000',
            '-ac', '1',
            '-c:a', 'pcm_s16le',
            audio_path
        ]
        
        run_ffmpeg_command(command)

        if not verify_file_integrity(audio_path):
            logger.error(f"Job {job_id}: El archivo de audio para transcripción no es válido o no se creó: {audio_path}")
            raise ProcessingError("El archivo de audio para transcripción no es válido")
        
        result = {
            "message": "La transcripción requiere integración con Whisper u otro servicio de ASR",
            "audio_prepared_path": audio_path,
            "requested_format": output_format,
            "language": language,
            "job_id": job_id
        }
        
        logger.info(f"Job {job_id}: Transcripción completada (simulada)")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, str(result))
        
        return result
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error transcribiendo media: {str(e)}")
        
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        raise
        
    finally:
        for file_path in [media_path, audio_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Error eliminando archivo temporal {file_path}: {str(e)}")
