import os
import logging
import uuid
import time
from ..utils.file_utils import download_file, generate_temp_filename
from ..services.ffmpeg_service import run_ffmpeg_command
from ..services.storage_service import store_file
from ..config import settings

logger = logging.getLogger(__name__)

def add_captions_to_video(
    video_url: str,
    subtitles_url: str,
    font: str = 'Arial',
    font_size: int = 24,
    font_color: str = 'white',
    background: bool = True,
    position: str = 'bottom',
    job_id: str = None,
    webhook_url: str = None
) -> str:
    """
    Añade subtítulos a un video.
    
    Args:
        video_url: URL del video
        subtitles_url: URL del archivo de subtítulos (SRT, VTT)
        font: Nombre de la fuente para los subtítulos
        font_size: Tamaño de la fuente
        font_color: Color de la fuente
        background: Si debe tener fondo detrás del texto
        position: Posición de los subtítulos (bottom, top)
        job_id: ID del trabajo
        webhook_url: URL para notificar cuando se complete
    
    Returns:
        str: URL del video con subtítulos
    """
    # Generar ID de trabajo si no se proporciona
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Procesando video con subtítulos desde {video_url}")
    
    try:
        # Descargar archivos
        video_path = download_file(video_url, settings.TEMP_DIR)
        subtitles_path = download_file(subtitles_url, settings.TEMP_DIR)
        
        logger.info(f"Job {job_id}: Archivos descargados correctamente")
        
        # Verificar extensión de subtítulos
        subtitle_ext = os.path.splitext(subtitles_path)[1].lower()
        if subtitle_ext not in ['.srt', '.vtt', '.ass', '.ssa']:
            raise ValueError(f"Formato de subtítulos no soportado: {subtitle_ext}. Formatos soportados: .srt, .vtt, .ass, .ssa")
        
        # Preparar ruta de salida
        output_path = generate_temp_filename(prefix=f"{job_id}_captioned_", suffix=".mp4")
        
        # Construir filtro de subtítulos
        if subtitle_ext in ['.srt', '.vtt']:
            # Configuración para SRT/VTT
            filter_options = []
            
            # Configuraciones específicas
            if font:
                filter_options.append(f"fontname={font}")
            
            filter_options.append(f"fontsize={font_size}")
            filter_options.append(f"fontcolor={font_color}")
            
            if background:
                filter_options.append("force_style='BackColour=&H80000000,Outline=0'")
            
            if position == "top":
                filter_options.append("marginv=20")
            else:  # bottom (default)
                filter_options.append("marginv=30")
            
            # Construir filtro
            subtitle_filter = f"subtitles={subtitles_path}:{':'.join(filter_options)}"
        else:  # .ass, .ssa
            # Para formatos ASS/SSA, simplemente usamos el archivo directamente
            subtitle_filter = f"ass={subtitles_path}"
        
        # Comando FFmpeg
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vf', subtitle_filter,
            '-c:a', 'copy',
            '-y', output_path
        ]
        
        # Ejecutar FFmpeg
        run_ffmpeg_command(command)
        
        # Almacenar archivo procesado
        result_url = store_file(output_path)
        
        # Limpieza de archivos temporales
        for file_path in [video_path, subtitles_path, output_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Error eliminando archivo temporal {file_path}: {e}")
        
        logger.info(f"Job {job_id}: Video con subtítulos procesado correctamente")
        
        # TODO: Implementar envío de webhook si se proporciona webhook_url
        
        return result_url
    
    except Exception as e:
        logger.exception(f"Job {job_id}: Error en add_captions_to_video: {str(e)}")
        # Limpieza en caso de error
        for file_path in [
            video_path if 'video_path' in locals() else None,
            subtitles_path if 'subtitles_path' in locals() else None,
            output_path if 'output_path' in locals() else None
        ]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        raise

def process_meme_overlay(
    video_url: str,
    meme_url: str,
    position: str = 'bottom',
    scale: float = 0.3,
    job_id: str = None,
    webhook_url: str = None
) -> str:
    """
    Superpone una imagen de meme sobre un video.
    
    Args:
        video_url: URL del video
        meme_url: URL de la imagen de meme
        position: Posición del meme (top, bottom, left, right, top_left, top_right, bottom_left, bottom_right, center)
        scale: Escala del meme relativa al video (0.1 a 1.0)
        job_id: ID del trabajo
        webhook_url: URL para notificar cuando se complete
    
    Returns:
        str: URL del video con meme
    """
    # Generar ID de trabajo si no se proporciona
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Procesando video con meme overlay desde {video_url}")
    
    try:
        # Validar parámetros
        valid_positions = ['top', 'bottom', 'left', 'right', 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'center']
        if position not in valid_positions:
            raise ValueError(f"Posición no válida. Debe ser una de: {', '.join(valid_positions)}")
        
        if not 0.1 <= scale <= 1.0:
            raise ValueError(f"Escala no válida: {scale}. Debe estar entre 0.1 y 1.0")
        
        # Descargar archivos
        video_path = download_file(video_url, settings.TEMP_DIR)
        meme_path = download_file(meme_url, settings.TEMP_DIR)
        
        logger.info(f"Job {job_id}: Archivos descargados correctamente")
        
        # Preparar ruta de salida
        output_path = generate_temp_filename(prefix=f"{job_id}_meme_", suffix=".mp4")
        
        # Definir coordenadas según la posición
        # Esto es una simplificación; FFmpeg usa expresiones más complejas para posicionar
        positions = {
            'top_left': 'x=10:y=10',
            'top': 'x=(main_w-overlay_w)/2:y=10',
            'top_right': 'x=main_w-overlay_w-10:y=10',
            'left': 'x=10:y=(main_h-overlay_h)/2',
            'center': 'x=(main_w-overlay_w)/2:y=(main_h-overlay_h)/2',
            'right': 'x=main_w-overlay_w-10:y=(main_h-overlay_h)/2',
            'bottom_left': 'x=10:y=main_h-overlay_h-10',
            'bottom': 'x=(main_w-overlay_w)/2:y=main_h-overlay_h-10',
            'bottom_right': 'x=main_w-overlay_w-10:y=main_h-overlay_h-10'
        }
        
        position_str = positions[position]
        
        # Construir filtro complejo
        filter_complex = (
            f"[1:v]scale=main_w*{scale}:-1[overlay];"
            f"[0:v][overlay]{position_str}:eval=frame[out]"
        )
        
        # Comando FFmpeg
        command = [
            'ffmpeg',
            '-i', video_path,
            '-i', meme_path,
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-map', '0:a?',  # Mapear audio del video original si existe
            '-c:a', 'copy',  # Mantener audio sin cambios
            '-y', output_path
        ]
        
        # Ejecutar FFmpeg
        run_ffmpeg_command(command)
        
        # Almacenar archivo procesado
        result_url = store_file(output_path)
        
        # Limpieza de archivos temporales
        for file_path in [video_path, meme_path, output_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Error eliminando archivo temporal {file_path}: {e}")
        
        logger.info(f"Job {job_id}: Video con meme overlay procesado correctamente")
        
        # TODO: Implementar envío de webhook si se proporciona webhook_url
        
        return result_url
    
    except Exception as e:
        logger.exception(f"Job {job_id}: Error en process_meme_overlay: {str(e)}")
        # Limpieza en caso de error
        for file_path in [
            video_path if 'video_path' in locals() else None,
            meme_path if 'meme_path' in locals() else None,
            output_path if 'output_path' in locals() else None
        ]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        raise
