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
from src.api.middlewares.error_handler import ProcessingError # Asegúrate que esta importación sea correcta

logger = logging.getLogger(__name__)

def extract_audio(media_url: str, bitrate: str = '192k', format: str = 'mp3', job_id: str = None, webhook_url: str = None) -> str:
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


        # Usamos os.path.join para construir rutas de forma segura
        output_filename = generate_temp_filename(prefix=f"{job_id}_audio_", suffix=f".{format}", temp_dir=settings.TEMP_DIR)
        output_path = os.path.join(settings.TEMP_DIR, output_filename)
        
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
            # Para AAC, es común especificar el bitrate también con -b:a, que ya está.
            # Algunos encoders pueden preferir -c:a aac_at (macOS) o libfdk_aac (si está compilado)
            command.extend(['-codec:a', 'aac']) 
        elif format == 'flac':
            command.extend(['-codec:a', 'flac'])
        
        # Ruta de salida
        command.append(output_path)
        
        # Ejecutar FFmpeg
        run_ffmpeg_command(command)
        
        # Verificar archivo de salida
        if not verify_file_integrity(output_path):
            logger.error(f"Job {job_id}: El archivo de audio extraído no es válido o no se creó: {output_path}")
            raise ProcessingError("El archivo de audio extraído no es válido")
        
        # Almacenar archivo de audio
        result_url = store_file(output_path) # Asume que store_file toma la ruta completa
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
        
        # Re-lanzar excepción para que sea manejada por el error_handler global o el endpoint
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

def transcribe_media(media_url: str, language: str = 'auto', output_format: str = 'txt', job_id: str = None, webhook_url: str = None) -> dict:
    """
    Transcribe audio de un archivo multimedia
    
    Args:
        media_url: URL del archivo multimedia
        language: Código de idioma o "auto"
        output_format: Formato de salida (txt, srt, vtt, json)
        job_id: ID de trabajo opcional
        webhook_url: URL para notificación de finalización
    
    Returns:
        dict: Información de transcripción o URL del archivo de transcripción (actualmente placeholder)
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
audio_path = generate_temp_filename(prefix=f"{job_id}_audio_transcribe_", suffix=".wav")

        # Usamos os.path.join para construir rutas de forma segura
        audio_filename = generate_temp_filename(prefix=f"{job_id}_audio_transcribe_", suffix=".wav", temp_dir=settings.TEMP_DIR)
        audio_path = os.path.join(settings.TEMP_DIR, audio_filename)
        
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

        # Verificar archivo de audio intermedio
        if not verify_file_integrity(audio_path):
            logger.error(f"Job {job_id}: El archivo de audio para transcripción no es válido o no se creó: {audio_path}")
            raise ProcessingError("El archivo de audio para transcripción no es válido")
        
        # Aquí iría la integración con Whisper o servicio de transcripción
        # Por ahora, devolvemos un mensaje placeholder
        
        result = {
            "message": "La transcripción requiere integración con Whisper u otro servicio de ASR",
            "audio_prepared_path": audio_path, # Podría ser útil para depuración o si el servicio de transcripción lo necesita
            "requested_format": output_format,
            "language": language,
            "job_id": job_id
        }
        
        # En una implementación real, el resultado de la transcripción se procesaría aquí.
        # Si el output_format es un archivo (srt, vtt, json), se generaría ese archivo,
        # se almacenaría con store_file() y se devolvería la URL.
        # Si es 'txt', se podría devolver el texto directamente en el JSON.
        
        logger.info(f"Job {job_id}: Transcripción completada (simulada)")
        
        # Enviar notificación si se solicita
        if webhook_url:
            # Para una implementación real, el payload de la notificación sería más útil
            # por ejemplo, la transcripción misma o la URL al archivo de transcripción.
            notify_job_completed(job_id, webhook_url, str(result)) # O un subconjunto más relevante de 'result'
        
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
        for file_path in [media_path, audio_path]: # audio_path es el .wav intermedio
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Job {job_id}: Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Error eliminando archivo temporal {file_path}: {str(e)}")
