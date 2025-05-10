# --- START OF FILE ffmpeg_service.py ---

import subprocess
import logging
import os
from typing import List, Dict, Optional, Any
import uuid
from ..config import settings
from ..api.middlewares.error_handler import ProcessingError

logger = logging.getLogger(__name__)

def run_ffmpeg_command(command: List[str], timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Ejecuta un comando FFmpeg de forma segura.
    
    Args:
        command (List[str]): Comando FFmpeg como lista de argumentos
        timeout (int, optional): Timeout en segundos
        
    Returns:
        Dict[str, Any]: Información sobre la ejecución
    
    Raises:
        ProcessingError: Si el comando falla
    """
    # Verificar que el primer elemento sea ffmpeg
    if not command[0] == 'ffmpeg':
        command.insert(0, 'ffmpeg')
    
    # Asegurar que hay -y para sobreescribir archivos
    if '-y' not in command:
        command.insert(1, '-y')
    
    # Agregar threads para optimizar rendimiento
    threads_added = False
    for i, arg in enumerate(command):
        if arg in ['-threads']:
            threads_added = True
            break
    
    if not threads_added:
        command.extend(['-threads', str(settings.FFMPEG_THREADS)])
    
    # Establecer timeout
    effective_timeout = timeout or settings.FFMPEG_TIMEOUT
    
    # Ejecutar comando
    logger.debug(f"Ejecutando FFmpeg: {' '.join(command)}")
    
    start_time = os.times()
    
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            timeout=effective_timeout
        )
        
        # Calcular tiempo de CPU utilizado
        end_time = os.times()
        cpu_time = (end_time.user - start_time.user) + (end_time.system - start_time.system)
        
        logger.debug(f"Comando FFmpeg ejecutado correctamente (CPU time: {cpu_time:.2f}s)")
        
        # Verificar archivo de salida
        output_path = command[-1]
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise ProcessingError(
                f"FFmpeg completó correctamente pero el archivo de salida '{output_path}' está vacío o no existe",
                details={"command": command, "output_path": output_path}
            )
        
        return {
            "success": True,
            "output_path": output_path,
            "cpu_time": cpu_time,
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    except subprocess.TimeoutExpired as e:
        logger.error(f"Timeout ejecutando FFmpeg después de {effective_timeout}s")
        raise ProcessingError(
            f"Timeout ejecutando FFmpeg después de {effective_timeout} segundos",
            details={"command": command, "timeout": effective_timeout}
        )
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error ejecutando FFmpeg (código {e.returncode}): {e.stderr}")
        # --- LÍNEA MODIFICADA ---
        # Se usa splitlines() y se añade una comprobación para evitar IndexError si la lista está vacía
        last_line_stderr = e.stderr.strip().splitlines()[-1] if e.stderr.strip().splitlines() else e.stderr.strip()
        raise ProcessingError(
            f"Error ejecutando FFmpeg: {last_line_stderr}",
            details={"command": command, "return_code": e.returncode, "stderr": e.stderr}
        )
    
    except Exception as e:
        logger.exception(f"Error inesperado ejecutando FFmpeg: {str(e)}")
        raise ProcessingError(
            f"Error inesperado ejecutando FFmpeg: {str(e)}",
            details={"command": command}
        )

def get_media_info(file_path: str) -> Dict[str, Any]:
    """
    Obtiene información de un archivo multimedia usando ffprobe.
    
    Args:
        file_path (str): Ruta al archivo multimedia
        
    Returns:
        Dict[str, Any]: Información del archivo
    
    Raises:
        ProcessingError: Si ffprobe falla
    """
    if not os.path.exists(file_path):
        raise ProcessingError(
            f"El archivo '{file_path}' no existe",
            details={"file_path": file_path}
        )
    
    try:
        command = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            timeout=30
        )
        
        # Parsear salida JSON
        import json
        info = json.loads(result.stdout)
        
        # Extraer información relevante
        media_info = {
            'format': info.get('format', {}).get('format_name', 'unknown'),
            'duration': float(info.get('format', {}).get('duration', 0)),
            'size': int(info.get('format', {}).get('size', 0)),
            'bit_rate': int(info.get('format', {}).get('bit_rate', 0)),
            'streams': []
        }
        
        # Analizar streams
        for stream in info.get('streams', []):
            stream_type = stream.get('codec_type')
            
            if stream_type == 'video':
                media_info['streams'].append({
                    'type': 'video',
                    'codec': stream.get('codec_name', 'unknown'),
                    'width': int(stream.get('width', 0)),
                    'height': int(stream.get('height', 0)),
                    'fps': eval(stream.get('r_frame_rate', '0/1')) if stream.get('r_frame_rate') else 0,
                })
                
                # Actualizar info principal con datos del primer stream de video
                if 'width' not in media_info and stream.get('width'):
                    media_info['width'] = int(stream.get('width', 0))
                    media_info['height'] = int(stream.get('height', 0))
                    media_info['video_codec'] = stream.get('codec_name')
                    
            elif stream_type == 'audio':
                media_info['streams'].append({
                    'type': 'audio',
                    'codec': stream.get('codec_name', 'unknown'),
                    'channels': int(stream.get('channels', 0)),
                    'sample_rate': int(stream.get('sample_rate', 0)),
                })
                
                # Actualizar info principal con datos del primer stream de audio
                if 'audio_codec' not in media_info:
                    media_info['audio_codec'] = stream.get('codec_name')
                    media_info['audio_channels'] = int(stream.get('channels', 0))
        
        return media_info
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error ejecutando ffprobe: {e.stderr}")
        raise ProcessingError(
            f"Error obteniendo información multimedia: {e.stderr}",
            details={"file_path": file_path, "stderr": e.stderr}
        )
    
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON de ffprobe: {str(e)}")
        raise ProcessingError(
            f"Error decodificando información multimedia: {str(e)}",
            details={"file_path": file_path, "stdout": result.stdout if 'result' in locals() else ''}
        )
    
    except Exception as e:
        logger.exception(f"Error inesperado en get_media_info: {str(e)}")
        raise ProcessingError(
            f"Error inesperado obteniendo información multimedia: {str(e)}",
            details={"file_path": file_path}
        )

# Definición completa de compose_ffmpeg
# (Asumiendo que funciones como download_file, generate_temp_filename, etc.,
# están definidas o importadas en otra parte de este módulo o son accesibles globalmente)
def compose_ffmpeg(inputs, filter_complex, output_options=None, job_id=None, webhook_url=None):
    """
    Realiza una composición avanzada con FFmpeg.
    
    Args:
        inputs: Lista de entradas (URLs y opciones)
        filter_complex: Filtro complejo de FFmpeg
        output_options: Opciones para la salida
        job_id: ID de trabajo opcional
        webhook_url: URL para notificación de finalización
    
    Returns:
        str: URL del archivo procesado
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"Job {job_id}: Iniciando composición FFmpeg con {len(inputs)} entradas")
    
    input_paths = []
    output_path = None
    
    # Estas funciones deben ser importadas o definidas para que compose_ffmpeg funcione
    # from ..utils.file_utils import download_file, generate_temp_filename
    # from ..services.storage_service import store_file
    # from ..services.webhook_service import notify_job_completed, notify_job_failed
    # from ..services.ffmpeg_service import verify_file_integrity (ya está en este módulo si se define)

    # Placeholder para verify_file_integrity si no está definido en este mismo archivo
    # Debería ser importado o definido correctamente en un escenario real
    def verify_file_integrity(file_path: str) -> bool:
        logger.warning("verify_file_integrity no está completamente implementada en este contexto de ejemplo.")
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
        
    # Placeholder para download_file
    def download_file(url: str, temp_dir: str, prefix: Optional[str] = None) -> str:
        logger.warning(f"download_file no está completamente implementada en este contexto de ejemplo. Simulando descarga de {url}")
        # Simular descarga creando un archivo temporal vacío
        temp_file_name = (prefix or "") + os.path.basename(url)
        dummy_path = os.path.join(temp_dir, temp_file_name if temp_file_name else "dummy_download.tmp")
        # Asegurarse de que el directorio temporal exista
        os.makedirs(temp_dir, exist_ok=True)
        with open(dummy_path, 'w') as f:
            f.write("dummy content") # Escribir algo para que no tenga tamaño 0
        return dummy_path

    # Placeholder para generate_temp_filename
    def generate_temp_filename(prefix: str = "", suffix: str = "") -> str:
        logger.warning("generate_temp_filename no está completamente implementada en este contexto de ejemplo.")
        # Asegurarse de que el directorio temporal exista
        os.makedirs(settings.TEMP_DIR, exist_ok=True)
        return os.path.join(settings.TEMP_DIR, f"{prefix}{uuid.uuid4()}{suffix}")

    # Placeholder para store_file
    def store_file(file_path: str) -> str:
        logger.warning(f"store_file no está completamente implementada en este contexto de ejemplo. Simulando almacenamiento de {file_path}")
        return f"http://fake-storage.com/{os.path.basename(file_path)}"

    # Placeholder para notify_job_completed
    def notify_job_completed(job_id: str, webhook_url: str, result_url: str):
        logger.warning(f"notify_job_completed no implementada. Job: {job_id}, Webhook: {webhook_url}, Result: {result_url}")

    # Placeholder para notify_job_failed
    def notify_job_failed(job_id: str, webhook_url: str, error_message: str):
        logger.warning(f"notify_job_failed no implementada. Job: {job_id}, Webhook: {webhook_url}, Error: {error_message}")


    try:
        # Validar parámetros
        if not filter_complex:
            raise ValueError("Se requiere el parámetro filter_complex")
        
        # Descargar archivos de entrada
        for i, input_data in enumerate(inputs):
            url = input_data["url"]
            path = download_file(url, settings.TEMP_DIR) 
            input_paths.append(path)
            logger.info(f"Job {job_id}: Entrada {i+1}/{len(inputs)} descargada: {path}")
        
        # Preparar ruta de salida
        output_path = generate_temp_filename(prefix=f"{job_id}_ffmpeg_", suffix=".mp4")
        
        # Construir comando FFmpeg
        ffmpeg_command_list = [] # No iniciar con 'ffmpeg' aquí, run_ffmpeg_command lo hará
        
        # Añadir entradas con sus opciones
        for i, (path, input_data) in enumerate(zip(input_paths, inputs)):
            if "options" in input_data and input_data["options"]:
                ffmpeg_command_list.extend(input_data["options"])
            ffmpeg_command_list.extend(['-i', path])
        
        # Añadir filtro complejo
        ffmpeg_command_list.extend(['-filter_complex', filter_complex])
        
        # Añadir opciones de salida
        if output_options:
            ffmpeg_command_list.extend(output_options)
        
        # Añadir ruta de salida
        ffmpeg_command_list.append(output_path)
        
        # Ejecutar FFmpeg
        run_ffmpeg_command(ffmpeg_command_list) # Esta función ya está definida en este archivo
        
        # Verificar archivo de salida
        if not verify_file_integrity(output_path):
            raise ProcessingError("El archivo de salida FFmpeg no es válido")
        
        # Almacenar archivo procesado
        result_url = store_file(output_path)
        logger.info(f"Job {job_id}: Composición FFmpeg completada y almacenada: {result_url}")
        
        # Enviar notificación si se solicita
        if webhook_url:
            notify_job_completed(job_id, webhook_url, result_url)
        
        return result_url
        
    except Exception as e:
        logger.exception(f"Job {job_id}: Error en composición FFmpeg: {str(e)}")
        
        # Enviar notificación de error si se solicita
        if webhook_url:
            notify_job_failed(job_id, webhook_url, str(e))
        
        # Re-lanzar excepción
        raise
        
    finally:
        # Limpiar archivos temporales
        for path in input_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e_clean: # Renombrar para evitar conflicto con la 'e' del except principal
                    logger.warning(f"Error eliminando archivo temporal {path}: {str(e_clean)}")
        
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception as e_clean: # Renombrar para evitar conflicto
                logger.warning(f"Error eliminando archivo temporal {output_path}: {str(e_clean)}")

# --- END OF FILE ffmpeg_service.py ---
