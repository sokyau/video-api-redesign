import os
import requests
import uuid
import logging
import re
import shutil
from typing import Optional
from urllib.parse import urlparse, unquote
from ..config import settings
from ..api.middlewares.error_handler import ValidationError, ProcessingError, NotFoundError

logger = logging.getLogger(__name__)

def download_file(url: str, target_dir: Optional[str] = None, prefix: Optional[str] = None) -> str:
    """
    Descarga un archivo desde una URL.
    
    Args:
        url (str): URL del archivo a descargar
        target_dir (str, optional): Directorio donde guardar el archivo
        
    Returns:
        str: Ruta al archivo descargado
        
    Raises:
        ValidationError: Si la URL no es válida
        ProcessingError: Si ocurre un error durante la descarga
    """
    # Validar URL
    if not url or not isinstance(url, str):
        raise ValidationError("La URL no puede estar vacía o no ser una cadena de texto")
    
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValidationError(f"URL inválida: {url}")
        
        if parsed_url.scheme not in ['http', 'https']:
            raise ValidationError(f"Esquema de URL no permitido: {parsed_url.scheme}")
    except Exception as e:
        raise ValidationError(f"Error validando URL: {str(e)}")
    
    # Determinar directorio destino
    if not target_dir:
        target_dir = settings.TEMP_DIR
    
    # Asegurar que el directorio existe
    os.makedirs(target_dir, exist_ok=True)
    
    # Determinar nombre de archivo de salida
    filename = os.path.basename(unquote(parsed_url.path))
    if not filename or '.' not in filename:
        # Generar nombre aleatorio con extensión si no se puede determinar
        filename = f"{uuid.uuid4()}.tmp"
    
    file_path = os.path.join(target_dir, filename)

# Aplicar prefijo si se proporciona
if prefix:
    basename = os.path.basename(file_path)
    dirname = os.path.dirname(file_path)
    file_path = os.path.join(dirname, f"{prefix}{basename}")
    
    try:
        # Realizar la descarga
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            
            # Verificar tamaño máximo
            content_length = response.headers.get('Content-Length')
            max_size = 1024 * 1024 * 1024  # 1GB
            if content_length and int(content_length) > max_size:
                raise ValidationError(f"El archivo es demasiado grande: {int(content_length)} bytes")
            
            # Guardar archivo por chunks para manejar archivos grandes
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        logger.debug(f"Archivo descargado: {url} -> {file_path}")
        return file_path
        
    except requests.RequestException as e:
        logger.error(f"Error descargando archivo {url}: {str(e)}")
        # Limpiar archivo parcial si existe
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise ProcessingError(f"Error descargando archivo: {str(e)}")
    
    except Exception as e:
        logger.exception(f"Error inesperado descargando {url}: {str(e)}")
        # Limpiar archivo parcial si existe
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise ProcessingError(f"Error inesperado durante la descarga: {str(e)}")

def generate_temp_filename(prefix: str = "", suffix: str = "") -> str:
    """
    Genera un nombre de archivo temporal único.
    
    Args:
        prefix (str): Prefijo para el nombre de archivo
        suffix (str): Sufijo/extensión para el archivo
        
    Returns:
        str: Ruta completa al archivo temporal
    """
    unique_id = str(uuid.uuid4())
    filename = f"{prefix}{unique_id}{suffix}"
    return os.path.join(settings.TEMP_DIR, filename)

def is_valid_filename(filename: str) -> bool:
    """
    Verifica si un nombre de archivo es válido y seguro.
    
    Args:
        filename (str): Nombre de archivo a verificar
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if not filename or not isinstance(filename, str):
        return False
    
    # Verificar caracteres no permitidos
    if re.search(r'[<>:"/\\|?*\x00-\x1F]', filename):
        return False
    
    # Verificar path traversal
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        return False
    
    return True

def safe_delete_file(file_path: str) -> bool:
    """
    Elimina un archivo de forma segura.
    
    Args:
        file_path (str): Ruta al archivo a eliminar
        
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    if not file_path or not os.path.exists(file_path):
        return True  # No existe, consideramos éxito
    
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        logger.error(f"Error eliminando archivo {file_path}: {str(e)}")
        return False

def get_file_extension(file_path: str) -> str:
    """
    Obtiene la extensión de un archivo.
    
    Args:
        file_path (str): Ruta o nombre del archivo
        
    Returns:
        str: Extensión del archivo (con punto)
    """
    _, extension = os.path.splitext(file_path)
    return extension.lower()

def verify_file_integrity(file_path):
    """
    Verifica la integridad de un archivo.
    
    Args:
        file_path (str): Ruta al archivo
    
    Returns:
        bool: True si el archivo es válido, False en caso contrario
    """
    if not os.path.exists(file_path):
        return False
    
    if os.path.getsize(file_path) == 0:
        return False
    
    # Verificación adicional: intentar abrir el archivo
    try:
        with open(file_path, 'rb') as f:
            # Leer los primeros bytes para verificar que se puede acceder
            f.read(1024)
        return True
    except Exception as e:
        logger.error(f"Error verificando integridad de archivo {file_path}: {str(e)}")
        return False
