# src/services/media_service.py
import os
import logging
import time
import uuid
from src.utils.file_utils import download_file, generate_temp_filename, verify_file_integrity
from src.services.ffmpeg_service import run_ffmpeg_command, get_media_info
from src.services.storage_service import store_file
from src.services.webhook_service import notify_job_completed, notify_job_failed
from src.config import settings
from src.api.middlewares.error_handler import ProcessingError

logger = logging.getLogger(__name__)

def extract_audio(media_url, bitrate='192k', format='mp3', job_id=None, webhook_url=None):
    """
    Extrae audio de un archivo multimedia
    
    Args:
        media_url: URL del archivo multimedia
        bitrate: Bitrate del audio (p.ej. "192k")
        format: Formato del audio (mp3, wav, etc.)
        job_id: ID de trabajo opcional
        webhook_url: URL para notificación de finalización
    
    Returns:
        str: URL del archivo de audio extraído
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando extracción de audio desde {media_url}")
    
    media_path = None
    output_path = None
    
    try:
        # Descargar archivo multimedia
        media_path = download_file(media_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Archivo multimedia descargado: {media_path}")
        
        # Verificar que es un archivo multimedia válido
        media_info = get_media_info(media_path)
        logger.debug(f"Job {job_id}: Información multimedia: {media_info}")
        
        # Preparar ruta de salida
        output_path = generate_temp_filename(prefix=f"{job_id}_audio_", suffix=f".{format}")
        
        # Construir comando FFmpeg
        command = [
            'ffmpeg',
            '-i', media_path,
            '-vn',  # No video
            '-b:a', bitrate
        ]
        
        # Añadir opciones específicas según formato
        if format == 'mp3':
            command.extend(['-codec:a', 'libmp3lame', '-q:a', '2'])
        elif format == 'wav':
            command.extend(['-codec:a', 'pcm_s16le'])
        elif format == 'aac':
            command.extend(['-codec:a', 'aac', '-b:a', bitrate])
        elif format == 'flac':
            command.extend(['-codec:a', 'flac'])
        
        # Ruta de salida
        command.append(output_path)
        
        # Ejecutar FFmpeg
        run_ffmpeg_command(command)
        
        # Verificar archivo de salida
        if not verify_file_integrity(output_path):
            raise ProcessingError("El archivo de audio extraído no es válido")
        
        # Almacenar archivo de audio
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Audio extraído y almacenado: {result_url}")
        
        # Enviar notificación si se solicita
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error extrayendo audio: {str(e)}")
        
        # Enviar notificación de error si se solicita
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        # Re-lanzar excepción
        raise
        
    finally:
        # Limpiar archivos temporales
        for file_path in [media_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Error eliminando archivo temporal {file_path}: {str(e)}")

def transcribe_media(media_url, language='auto', output_format='txt', job_id=None, webhook_url=None):
    """
    Transcribe audio de un archivo multimedia
    
    Args:
        media_url: URL del archivo multimedia
        language: Código de idioma o "auto"
        output_format: Formato de salida (txt, srt, vtt, json)
        job_id: ID de trabajo opcional
        webhook_url: URL para notificación de finalización
    
    Returns:
        dict: Información de transcripción o URL del archivo de transcripción
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando transcripción desde {media_url}")
    
    media_path = None
    audio_path = None
    
    try:
        # Descargar archivo multimedia
        media_path = download_file(media_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Archivo multimedia descargado: {media_path}")
        
        # Extraer audio para transcripción (WAV es mejor para Whisper)
        audio_path = generate_temp_filename(prefix=f"{job_id}_audio_", suffix=".wav")
        
        # Comando para extraer audio WAV de 16kHz (formato óptimo para Whisper)
        command = [
            'ffmpeg',
            '-i', media_path,
            '-vn',  # No video
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',  # Mono
            '-c:a', 'pcm_s16le',  # PCM signed 16-bit little-endian
            audio_path
        ]
        
        # Ejecutar FFmpeg
        run_ffmpeg_command(command)
        
        # Aquí iría la integración con Whisper o servicio de transcripción
        # Por ahora, devolvemos un mensaje placeholder
        
        result = {
            "message": "La transcripción requiere integración con Whisper u otro servicio de ASR",
            "audio_prepared": True,
            "requested_format": output_format,
            "language": language
        }
        
        # En una implementación real, devolveríamos:
        # - Para output_format='txt': la transcripción como texto
        # - Para otros formatos: URL a un archivo de subtítulos
        
        logger.info(f"Job {job_id}: Transcripción completada (simulada)")
        
        # Enviar notificación si se solicita
        if webhook_url:
            notify_job_completed(job_id, webhook_url, str(result))
        
        return result
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error transcribiendo media: {str(e)}")
        
        # Enviar notificación de error si se solicita
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        # Re-lanzar excepción
        raise
        
    finally:
        # Limpiar archivos temporales
        for file_path in [media_path, audio_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Error eliminando archivo temporal {file_path}: {str(e)}")

