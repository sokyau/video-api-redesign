import os
import logging
import uuid
import time # Importado pero no usado directamente en el código nuevo, podría ser usado por dependencias
# --- LÍNEA MODIFICADA ---
from ..utils.file_utils import download_file, generate_temp_filename, verify_file_integrity
# --- LÍNEA MODIFICADA ---
from ..services.ffmpeg_service import run_ffmpeg_command
# --- LÍNEA ELIMINADA (verify_file_integrity ya no se importa de ffmpeg_service) ---
from ..services.storage_service import store_file
from ..config import settings
from src.services.webhook_service import notify_job_completed, notify_job_failed
from src.api.middlewares.error_handler import ProcessingError

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
    
    video_path = None
    subtitles_path = None
    output_path = None

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
            
            escaped_subtitles_path = subtitles_path.replace('\\', '/').replace(':', '\\:')
            style_options_str = ','.join(filter_options)
            
            # Construir el string de force_style correctamente
            force_style_parts = []
            if font:
                 force_style_parts.append(f"FontName={font}")
            force_style_parts.append(f"FontSize={font_size}")
            # FFmpeg's subtitles filter uses 'PrimaryColour', 'BackColour' etc. for ASS-like styling.
            # The color format &HBBGGRR (hex BlueGreenRed) is common for ASS.
            # Convert common color names to this format or expect this format.
            # For simplicity, assuming font_color is directly usable or pre-formatted.
            force_style_parts.append(f"PrimaryColour=&HFFFFFF") # Default white, improve with color conversion
            if background:
                 force_style_parts.append(f"BackColour=&H80000000") # Semi-transparent black
            
            # Vertical margin for srt/vtt is not directly part of force_style in the same way as ASS.
            # FFmpeg's subtitles filter might have its own way or it might be limited.
            # 'marginv' is an option for the subtitles filter itself, not force_style.
            
            final_force_style = ','.join(force_style_parts)
            subtitle_filter_parts = [f"subtitles='{escaped_subtitles_path}'"]
            if final_force_style:
                subtitle_filter_parts.append(f"force_style='{final_force_style}'")

            # Add marginv directly to the filter options if applicable
            if position == "top":
                subtitle_filter_parts.append("marginv=20")
            else: # bottom
                subtitle_filter_parts.append("marginv=30")

            subtitle_filter = ':'.join(subtitle_filter_parts)

        else:  # .ass, .ssa
            escaped_subtitles_path = subtitles_path.replace('\\', '/').replace(':', '\\:')
            subtitle_filter = f"ass='{escaped_subtitles_path}'"
        
        command = [
            # ffmpeg command will be prepended by run_ffmpeg_command
            '-i', video_path,
            '-vf', subtitle_filter,
            '-c:a', 'copy',
            output_path # -y will be added by run_ffmpeg_command
        ]
        
        run_ffmpeg_command(command)
        
        if not verify_file_integrity(output_path):
            raise ProcessingError(f"El archivo de salida para subtítulos '{output_path}' no es válido o está vacío.")

        result_url = store_file(output_path)
        
        logger.info(f"Job {job_id}: Video con subtítulos procesado correctamente")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
    
    except Exception as e:
        logger.exception(f"Job {job_id}: Error en add_captions_to_video: {str(e)}")
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        raise
    finally:
        for file_path in [video_path, subtitles_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e_clean:
                    logger.warning(f"Job {job_id}: Error eliminando archivo temporal {file_path}: {e_clean}")


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
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Procesando video con meme overlay desde {video_url}")
    
    video_path = None
    meme_path = None
    output_path = None

    try:
        valid_positions = ['top', 'bottom', 'left', 'right', 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'center']
        if position not in valid_positions:
            raise ValueError(f"Posición no válida. Debe ser una de: {', '.join(valid_positions)}")
        
        if not 0.1 <= scale <= 1.0:
            raise ValueError(f"Escala no válida: {scale}. Debe estar entre 0.1 y 1.0")
        
        video_path = download_file(video_url, settings.TEMP_DIR)
        meme_path = download_file(meme_url, settings.TEMP_DIR)
        
        logger.info(f"Job {job_id}: Archivos descargados correctamente")
        
        output_path = generate_temp_filename(prefix=f"{job_id}_meme_", suffix=".mp4")
        
        positions_map = {
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
        
        position_overlay_expr = positions_map[position]
        
        filter_complex = (
            f"[1:v]scale=main_w*{scale}:-1[overlay_scaled];"
            f"[0:v][overlay_scaled]overlay={position_overlay_expr}[outv]" # Removed :eval=frame as it might not be needed for basic positioning
        )
        
        command = [
            '-i', video_path,
            '-i', meme_path,
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '0:a?', 
            '-c:a', 'copy',
            output_path
        ]
        
        run_ffmpeg_command(command)
        
        if not verify_file_integrity(output_path):
             raise ProcessingError("El archivo de video con meme overlay no es válido o está vacío.")

        result_url = store_file(output_path)
        
        logger.info(f"Job {job_id}: Video con meme overlay procesado correctamente")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
    
    except Exception as e:
        logger.exception(f"Job {job_id}: Error en process_meme_overlay: {str(e)}")
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        raise
    finally:
        for file_path in [video_path, meme_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e_clean:
                    logger.warning(f"Job {job_id}: Error eliminando archivo temporal {file_path}: {e_clean}")

def concatenate_videos_service(video_urls: list[str], job_id: str = None, webhook_url: str = None) -> str:
    """
    Concatena múltiples videos en uno solo.
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando concatenación de {len(video_urls)} videos")
    
    video_paths = []
    output_path = None
    list_file_path = None
    
    try:
        for i, url in enumerate(video_urls):
            path = download_file(url, settings.TEMP_DIR, prefix=f"{job_id}_video_{i}_")
            video_paths.append(path)
            logger.info(f"Job {job_id}: Video {i+1}/{len(video_urls)} descargado: {path}")
        
        list_file_path = os.path.join(settings.TEMP_DIR, f"{job_id}_concat_list.txt")
        with open(list_file_path, 'w', encoding='utf-8') as f:
            for path in video_paths:
                escaped_path = path.replace("'", "'\\''") 
                f.write(f"file '{escaped_path}'\n")
        
        output_path = generate_temp_filename(prefix=f"{job_id}_concat_", suffix=".mp4")
        
        command = [
            '-f', 'concat',
            '-safe', '0', 
            '-i', list_file_path,
            '-c', 'copy',
            output_path
        ]
        
        run_ffmpeg_command(command)
        
        if not verify_file_integrity(output_path):
            raise ProcessingError("El archivo de video concatenado no es válido o está vacío.")
        
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Videos concatenados y almacenados: {result_url}")
        
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error concatenando videos: {str(e)}")
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        raise
    finally:
        for path in video_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e_clean:
                    logger.warning(f"Job {job_id}: Error eliminando archivo temporal {path}: {e_clean}")
        
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception as e_clean:
                logger.warning(f"Job {job_id}: Error eliminando archivo temporal de salida {output_path}: {e_clean}")
        
        if list_file_path and os.path.exists(list_file_path):
            try:
                os.remove(list_file_path)
            except Exception as e_clean:
                logger.warning(f"Job {job_id}: Error eliminando archivo de lista temporal {list_file_path}: {e_clean}")

def animated_text_service(
    video_url: str,
    text: str,
    animation: str = "fade",
    position: str = "bottom",
    font: str = "Arial",
    font_size: int = 36,
    color: str = "white",
    duration: float = 3.0,
    job_id: str = None,
    webhook_url: str = None
) -> str:
    """
    Superpone texto animado sobre el video y devuelve la URL del resultado.
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando animación de texto para video {video_url}")
    
    video_path = None
    output_path = None

    try:
        video_path = download_file(video_url, settings.TEMP_DIR)
        output_path = generate_temp_filename(prefix=f"{job_id}_animated_text_", suffix=".mp4")

        escaped_text = text.replace('\\', '\\\\') \
                           .replace("'", "\u2019") \
                           .replace(":", "\\:") \
                           .replace(",", "\\,") \
                           .replace("%", "%%")

        padding_expr = "main_h*0.05" 
        if position == "bottom":
            pos_x = "(main_w-text_w)/2"
            pos_y = f"main_h-text_h-{padding_expr}"
        elif position == "top":
            pos_x = "(main_w-text_w)/2"
            pos_y = padding_expr
        elif position == "center":
            pos_x = "(main_w-text_w)/2"
            pos_y = "(main_h-text_h)/2"
        else: 
            logger.warning(f"Job {job_id}: Posición de texto '{position}' no reconocida, usando 'bottom'.")
            pos_x = "(main_w-text_w)/2"
            pos_y = f"main_h-text_h-{padding_expr}"

        base_drawtext_params = f"fontfile='{font}':text='{escaped_text}':fontsize={font_size}:fontcolor='{color}':x='{pos_x}':y='{pos_y}'"
        # Para fontfile, es mejor asegurarse de que la fuente esté disponible o proporcionar una ruta completa.
        # Si 'font' es solo un nombre como 'Arial', FFmpeg depende de la configuración de Fontconfig.

        text_anim_total_duration = duration 
        fade_effect_time = min(0.5, text_anim_total_duration * 0.2) 

        alpha_expression = (
            f"if(lt(t,0),0," # Invisible before start
            f"if(lt(t,{fade_effect_time}),t/{fade_effect_time},"  # Fade in
            f"if(lt(t,{text_anim_total_duration}-{fade_effect_time}),1,"  # Visible
            f"if(lt(t,{text_anim_total_duration}),({text_anim_total_duration}-t)/{fade_effect_time},0))))" # Fade out, then invisible
        )
        
        if animation not in ["fade", "slide", "zoom", "typewriter", "bounce"]:
            logger.warning(f"Job {job_id}: Animación '{animation}' no reconocida, usando 'fade' por defecto.")
        
        drawtext_filter_string = f"drawtext={base_drawtext_params}:alpha='{alpha_expression}':enable='between(t,0,{text_anim_total_duration})'"
        
        command = [
            '-i', video_path,
            '-vf', drawtext_filter_string,
            '-c:a', 'copy',
            output_path
        ]

        run_ffmpeg_command(command)
        
        if not verify_file_integrity(output_path):
            raise ProcessingError("El archivo de video con texto animado no es válido o está vacío.")

        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Video con texto animado procesado y almacenado: {result_url}")

        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url

    except Exception as e:
        logger.exception(f"Job {job_id}: Error en animated_text_service: {str(e)}")
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        for p in [video_path, output_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception as e_clean: 
                    logger.warning(f"Job {job_id}: Error eliminando archivo temporal {p} durante manejo de excepción: {e_clean}")
        raise
    finally:
        # Limpieza final (si no ocurrió una excepción que ya limpió los archivos)
        # El bloque except ya maneja la limpieza en caso de error.
        # Este finally limpiará si la función retorna normalmente.
        if 'e' not in locals() or e is None: # Solo limpiar si no hubo excepción o la limpieza ya se hizo
            for p in [video_path, output_path]:
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception as e_clean: 
                        logger.warning(f"Job {job_id}: Error eliminando archivo temporal {p} en finally: {e_clean}")

