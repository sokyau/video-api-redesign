import os
import logging
import uuid
import time # Importado pero no usado directamente en el código nuevo, podría ser usado por dependencias
from ..utils.file_utils import download_file, generate_temp_filename
from ..services.ffmpeg_service import run_ffmpeg_command, verify_file_integrity
from ..services.storage_service import store_file
from ..config import settings
from src.services.webhook_service import notify_job_completed, notify_job_failed
# --- LÍNEA MODIFICADA ---
# Se cambió la ruta de importación para la clase ProcessingError
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
                filter_options.append(f"fontname={font}") # fontname es más común para libass que fontfile para srt/vtt
            
            filter_options.append(f"fontsize={font_size}")
            filter_options.append(f"fontcolor={font_color}")
            
            if background:
                # Esta sintaxis de force_style es para libass, puede no aplicar directamente a SRT/VTT renderizado por 'subtitles' filter
                # Para 'subtitles' filter, background/box es a menudo controlado por 'box=1:boxcolor=black@0.5'
                filter_options.append("force_style='BackColour=&H80000000,Outline=0'") # Manteniendo original, pero revisar compatibilidad
            
            if position == "top":
                filter_options.append("marginv=20") # Distancia desde el borde superior/inferior
            else:  # bottom (default)
                filter_options.append("marginv=30")
            
            # Construir filtro
            # Asegurarse que el path de subtítulos está correctamente escapado para ffmpeg
            escaped_subtitles_path = subtitles_path.replace('\\', '/').replace(':', '\\:')
            subtitle_filter = f"subtitles='{escaped_subtitles_path}':force_style='{','.join(filter_options)}'"
            if not font: # Si no se especifica font, quitarlo de las opciones para no enviar fontname=''
                subtitle_filter = f"subtitles='{escaped_subtitles_path}':force_style='{','.join(o for o in filter_options if 'fontname' not in o)}'"


        else:  # .ass, .ssa
            # Para formatos ASS/SSA, simplemente usamos el archivo directamente
            escaped_subtitles_path = subtitles_path.replace('\\', '/').replace(':', '\\:')
            subtitle_filter = f"ass='{escaped_subtitles_path}'"
        
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
        # Limpieza de archivos temporales
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
    
    video_path = None
    meme_path = None
    output_path = None

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
        # Usar W y H para main video width/height, w y h para overlay width/height
        # main_w, main_h, overlay_w, overlay_h
        positions_map = {
            'top_left': 'x=10:y=10',
            'top': 'x=(main_w-overlay_w)/2:y=10',
            'top_right': 'x=main_w-overlay_w-10:y=10',
            'left': 'x=10:y=(main_h-overlay_h)/2',
            'center': 'x=(main_w-overlay_w)/2:y=(main_h-overlay_h)/2',
            'right': 'x=main_w-overlay_w-10:y=(main_h-overlay_h)/2',
            'bottom_left': 'x=10:y=main_h-overlay_h-10',
            'bottom': 'x=(main_w-overlay_w)/2:y=main_h-overlay_h-10', # Original
            'bottom_right': 'x=main_w-overlay_w-10:y=main_h-overlay_h-10'
        }
        
        position_overlay_expr = positions_map[position]
        
        # Construir filtro complejo
        # [1:v] es el segundo input (meme), [0:v] es el primer input (video)
        filter_complex = (
            f"[1:v]scale=main_w*{scale}:-1[overlay_scaled];" # Escalar el meme
            f"[0:v][overlay_scaled]overlay={position_overlay_expr}:eval=frame[outv]" # Superponer
        )
        
        # Comando FFmpeg
        command = [
            'ffmpeg',
            '-i', video_path,
            '-i', meme_path,
            '-filter_complex', filter_complex,
            '-map', '[outv]', # Mapear la salida de video del filter_complex
            '-map', '0:a?',  # Mapear audio del video original si existe, el '?' lo hace opcional
            '-c:a', 'copy',  # Mantener audio sin cambios
            '-y', output_path
        ]
        
        # Ejecutar FFmpeg
        run_ffmpeg_command(command)
        
        if not verify_file_integrity(output_path):
             raise ProcessingError("El archivo de video con meme overlay no es válido o está vacío.")

        # Almacenar archivo procesado
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
        # Limpieza de archivos temporales
        for file_path in [video_path, meme_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e_clean:
                    logger.warning(f"Job {job_id}: Error eliminando archivo temporal {file_path}: {e_clean}")

def concatenate_videos_service(video_urls: list[str], job_id: str = None, webhook_url: str = None) -> str:
    """
    Concatena múltiples videos en uno solo.
    
    Args:
        video_urls: Lista de URLs de videos
        job_id: ID de trabajo opcional
        webhook_url: URL para notificación de finalización
    
    Returns:
        str: URL del video concatenado
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando concatenación de {len(video_urls)} videos")
    
    video_paths = []
    output_path = None
    list_file_path = None # Definido para el finally
    
    try:
        # Descargar videos
        for i, url in enumerate(video_urls):
            # Usar un prefijo específico para los archivos descargados para evitar colisiones si son el mismo nombre de archivo
            path = download_file(url, settings.TEMP_DIR, prefix=f"{job_id}_video_{i}_")
            video_paths.append(path)
            logger.info(f"Job {job_id}: Video {i+1}/{len(video_urls)} descargado: {path}")
        
        # Generar archivo de lista para FFmpeg
        list_file_path = os.path.join(settings.TEMP_DIR, f"{job_id}_concat_list.txt")
        with open(list_file_path, 'w', encoding='utf-8') as f:
            for path in video_paths:
                # FFmpeg concat demuxer requiere que los paths estén correctamente escapados si contienen caracteres especiales.
                # Usar comillas simples alrededor del path es una práctica común.
                # Y escapar comillas simples dentro del path si las hubiera.
                escaped_path = path.replace("'", "'\\''") 
                f.write(f"file '{escaped_path}'\n")
        
        # Preparar ruta de salida
        output_path = generate_temp_filename(prefix=f"{job_id}_concat_", suffix=".mp4")
        
        # Comando FFmpeg para concatenación
        # -safe 0 es necesario si los paths no están bajo un directorio "seguro" conocido por FFmpeg.
        command = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0', 
            '-i', list_file_path,
            '-c', 'copy', # Copia los codecs, asume que los videos son compatibles
            '-y', # Sobrescribir archivo de salida si existe
            output_path
        ]
        
        # Ejecutar FFmpeg
        run_ffmpeg_command(command)
        
        # Verificar archivo de salida
        if not verify_file_integrity(output_path):
            raise ProcessingError("El archivo de video concatenado no es válido o está vacío.")
        
        # Almacenar archivo de video
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Videos concatenados y almacenados: {result_url}")
        
        # Enviar notificación si se solicita
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error concatenando videos: {str(e)}")
        
        # Enviar notificación de error si se solicita
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        # Re-lanzar excepción
        raise
    finally:
        # Limpiar archivos temporales
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
        
        # Eliminar archivo de lista
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

        # Escapar texto para FFmpeg drawtext filter
        # Reemplazar comilla simple con comilla tipográfica derecha para evitar problemas de quoting.
        # Escapar ':' y ',' ya que son separadores de opciones en el filtro.
        # Escapar '\' ya que es el carácter de escape de FFmpeg.
        # Escapar '%' ya que se usa para variables.
        escaped_text = text.replace('\\', '\\\\') \
                           .replace("'", "\u2019") \
                           .replace(":", "\\:") \
                           .replace(",", "\\,") \
                           .replace("%", "%%")

        # Posicionamiento del texto
        # Usar main_w, main_h, text_w, text_h para dimensiones
        # Padding como un porcentaje de la altura del video
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
        else: # Default to bottom
            logger.warning(f"Job {job_id}: Posición de texto '{position}' no reconocida, usando 'bottom'.")
            pos_x = "(main_w-text_w)/2"
            pos_y = f"main_h-text_h-{padding_expr}"

        # Parámetros comunes de drawtext
        # fontfile: FFmpeg intentará encontrar la fuente. Puede requerir la ruta completa o que Fontconfig esté configurado.
        # Para mayor robustez, se podría tener un directorio de fuentes y construir la ruta a fontfile.
        # Usar box=1:boxcolor=black@0.5 para un fondo semitransparente si se desea.
        base_drawtext_params = f"fontfile='{font}':text='{escaped_text}':fontsize={font_size}:fontcolor='{color}':x='{pos_x}':y='{pos_y}'"

        # Animación
        text_anim_total_duration = duration # Duración total de la visibilidad del texto
        fade_effect_time = min(0.5, text_anim_total_duration * 0.2) # Duración para fade in/out, e.g., 0.5s o 20%

        # Por defecto, todas las animaciones no implementadas específicamente usarán un fade in/out.
        # enable='between(t,start_time,end_time)' controla cuándo el texto es visible.
        # alpha controla la transparencia.
        alpha_expression = (
            f"if(lt(t,{fade_effect_time}),t/{fade_effect_time},"  # Fade in
            f"if(lt(t,{text_anim_total_duration}-{fade_effect_time}),1,"  # Visible
            f"if(lt(t,{text_anim_total_duration}),({text_anim_total_duration}-t)/{fade_effect_time},0)))" # Fade out
        )
        
        # Aquí se podrían añadir lógicas específicas para 'slide', 'zoom', 'typewriter', 'bounce'
        # modificando pos_x, pos_y, fontsize, o alpha con expresiones de tiempo más complejas.
        # Por ahora, todas usan el alpha_expression para un efecto de fade.
        if animation not in ["fade", "slide", "zoom", "typewriter", "bounce"]:
            logger.warning(f"Job {job_id}: Animación '{animation}' no reconocida, usando 'fade' por defecto.")
        
        # El texto se habilita desde t=0 hasta t=text_anim_total_duration
        drawtext_filter_string = f"drawtext={base_drawtext_params}:alpha='{alpha_expression}':enable='between(t,0,{text_anim_total_duration})'"
        
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vf', drawtext_filter_string,
            '-c:a', 'copy', # Copiar stream de audio sin recodificar
            '-y', # Sobrescribir archivo de salida
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
        # Limpieza en caso de error antes de re-lanzar
        for p in [video_path, output_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception as e_clean: # pragma: no cover
                    logger.warning(f"Job {job_id}: Error eliminando archivo temporal {p} durante manejo de excepción: {e_clean}")
        raise
    finally:
        # Limpieza final (si no ocurrió una excepción que ya limpió)
        for p in [video_path, output_path]:
            if p and os.path.exists(p) and not ('e' in locals() and e is not None) : # Solo si no hubo excepción o ya se limpió
                 if os.path.exists(p): # Doble chequeo por si se borró en el except
                    try:
                        os.remove(p)
                    except Exception as e_clean: # pragma: no cover
                        logger.warning(f"Job {job_id}: Error eliminando archivo temporal {p} en finally: {e_clean}")
