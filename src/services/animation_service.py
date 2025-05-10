# src/services/animation_service.py
import os
import logging
import uuid
from ..utils.file_utils import download_file, generate_temp_filename, verify_file_integrity
from ..services.ffmpeg_service import run_ffmpeg_command, get_media_info
from ..services.storage_service import store_file
from ..services.webhook_service import notify_job_completed, notify_job_failed
from ..config import settings
from ..api.middlewares.error_handler import ProcessingError

logger = logging.getLogger(__name__)

def animated_text_service(video_url, text, animation="fade", position="bottom", 
                     font="Arial", font_size=36, color="white", duration=3.0,
                     job_id=None, webhook_url=None):
    """
    Añade texto animado a un video.
    
    Args:
        video_url: URL del video base
        text: Texto a animar
        animation: Tipo de animación (fade, slide, zoom, typewriter, bounce)
        position: Posición del texto (top, bottom, center)
        font: Fuente del texto
        font_size: Tamaño de la fuente
        color: Color del texto
        duration: Duración de la animación en segundos
        job_id: ID de trabajo opcional
        webhook_url: URL para notificación de finalización
    
    Returns:
        str: URL del video procesado
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando procesamiento de texto animado en video {video_url}")
    
    video_path = None
    output_path = None
    
    try:
        # Descargar video
        video_path = download_file(video_url, settings.TEMP_DIR)
        logger.info(f"Job {job_id}: Video descargado: {video_path}")
        
        # Obtener info del video (duración, resolución)
        video_info = get_media_info(video_path)
        video_duration = float(video_info.get('duration', 0))
        video_width = int(video_info.get('width', 0))
        video_height = int(video_info.get('height', 0))
        
        if video_duration <= 0 or video_width <= 0 or video_height <= 0:
            raise ProcessingError("No se pudo obtener información del video")
        
        # Ajustar duración para que no exceda la duración del video
        if duration > video_duration:
            duration = video_duration
            logger.warning(f"Job {job_id}: Duración ajustada a {duration}s (duración del video)")
        
        # Preparar ruta de salida
        output_path = generate_temp_filename(prefix=f"{job_id}_animated_", suffix=".mp4")
        
        # Construir filtro FFmpeg según animación
        filter_complex = build_animation_filter(
            text, animation, position, font, font_size, color, 
            duration, video_width, video_height
        )
        
        # Comando FFmpeg
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vf', filter_complex,
            '-c:a', 'copy',
            output_path
        ]
        
        # Ejecutar FFmpeg
        run_ffmpeg_command(command)
        
        # Verificar archivo de salida
        if not verify_file_integrity(output_path):
            raise ProcessingError("El archivo de video con texto animado no es válido")
        
        # Almacenar archivo de video
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Video con texto animado procesado y almacenado: {result_url}")
        
        # Enviar notificación si se solicita
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error procesando texto animado: {str(e)}")
        
        # Enviar notificación de error si se solicita
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        # Re-lanzar excepción
        raise
        
    finally:
        # Limpiar archivos temporales
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception as e:
                logger.warning(f"Error eliminando archivo temporal {video_path}: {str(e)}")
        
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception as e:
                logger.warning(f"Error eliminando archivo temporal {output_path}: {str(e)}")

def build_animation_filter(text, animation, position, font, font_size, color, 
                          duration, video_width, video_height):
    """
    Construye filtro FFmpeg para texto animado.
    
    Args:
        text: Texto a animar
        animation: Tipo de animación
        position: Posición del texto
        font: Fuente del texto
        font_size: Tamaño de la fuente
        color: Color del texto
        duration: Duración de la animación
        video_width: Ancho del video
        video_height: Alto del video
    
    Returns:
        str: Filtro FFmpeg para drawtext
    """
    # Escapar caracteres especiales para FFmpeg
    text_escaped = text.replace("'", "\\'").replace(":", "\\:").replace(",", "\\,")
    
    # Determinar posición según parámetro
    if position == "top":
        y_pos = f"h*0.1"
    elif position == "bottom":
        y_pos = f"h*0.9"
    else:  # center
        y_pos = f"(h-text_h)/2"
    
    x_pos = f"(w-text_w)/2"  # Centrado horizontalmente
    
    # Base del filtro
    base_filter = f"drawtext=text='{text_escaped}':fontfile={font}:fontsize={font_size}:fontcolor={color}:x={x_pos}:y={y_pos}"
    
    # Aplicar animación
    if animation == "fade":
        # Fade in durante el primer segundo, fade out durante el último
        fade_time = min(1.0, duration / 3)
        alpha_expr = f"if(lt(t,{fade_time}),t/{fade_time},if(lt(t,{duration-fade_time}),1,({duration}-t)/{fade_time}))"
        return f"{base_filter}:alpha={alpha_expr}"
        
    elif animation == "slide":
        # Deslizar desde fuera de la pantalla
        slide_time = min(1.5, duration / 2)
        x_expr = f"if(lt(t,{slide_time}),w*1.5-((w*1.5-{x_pos})*t/{slide_time}),{x_pos})"
        return f"{base_filter}:x={x_expr}"
        
    elif animation == "zoom":
        # Zoom desde tamaño 0 hasta tamaño completo
        zoom_time = min(1.0, duration / 2)
        size_expr = f"if(lt(t,{zoom_time}),{font_size}*t/{zoom_time},{font_size})"
        return f"drawtext=text='{text_escaped}':fontfile={font}:fontsize={size_expr}:fontcolor={color}:x={x_pos}:y={y_pos}"
        
    elif animation == "typewriter":
        # Efecto máquina de escribir (aparición progresiva de letras)
        chars_per_sec = len(text) / duration
        # Este es un enfoque simplificado del efecto máquina de escribir
        return f"{base_filter}:enable='gte(t,0)'"
        
    elif animation == "bounce":
        # Efecto rebote (oscilación vertical)
        bounce_freq = 2.0  # Hz
        bounce_amp = font_size * 0.2  # 20% del tamaño de fuente
        decay = 2.0 / duration  # Decaimiento para que el rebote se detenga
        y_expr = f"{y_pos}+{bounce_amp}*exp(-{decay}*t)*sin(2*PI*{bounce_freq}*t)"
        return f"{base_filter}:y={y_expr}"
        
    else:
        # Sin animación o animación no reconocida
        return base_filter
