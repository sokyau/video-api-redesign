import os
import shutil
import uuid
from datetime import datetime
import logging
from ..config import settings
from ..utils.file_utils import is_valid_filename, safe_delete_file
from ..api.middlewares.error_handler import ValidationError, NotFoundError, ProcessingError

logger = logging.getLogger(__name__)

def ensure_storage_dir():
    """
    Asegura que el directorio de almacenamiento existe.
    
    Raises:
        ProcessingError: Si no se puede crear el directorio
    """
    try:
        os.makedirs(settings.STORAGE_PATH, exist_ok=True)
        logger.debug(f"Storage directory ensured: {settings.STORAGE_PATH}")
    except OSError as e:
        logger.error(f"Error creando directorio de almacenamiento {settings.STORAGE_PATH}: {str(e)}")
        raise ProcessingError(f"No se pudo crear el directorio de almacenamiento: {str(e)}")

def get_file_path(filename):
    """
    Obtiene la ruta completa de un archivo en el almacenamiento.
    
    Args:
        filename (str): Nombre del archivo
        
    Returns:
        str: Ruta completa al archivo
        
    Raises:
        ValidationError: Si el nombre de archivo no es válido
    """
    if not is_valid_filename(filename):
        raise ValidationError(f"Nombre de archivo inválido: {filename}")
    
    return os.path.join(settings.STORAGE_PATH, filename)

def get_file_url(filename):
    """
    Obtiene la URL pública de un archivo.
    
    Args:
        filename (str): Nombre del archivo
        
    Returns:
        str: URL pública del archivo
        
    Raises:
        ValidationError: Si el nombre de archivo no es válido
    """
    if not is_valid_filename(filename):
        raise ValidationError(f"Nombre de archivo inválido: {filename}")
    
    return f"{settings.BASE_URL}/{filename}"

def store_file(file_path, custom_filename=None):
    """
    Almacena un archivo en el almacenamiento permanente.
    
    Args:
        file_path (str): Ruta al archivo temporal
        custom_filename (str, optional): Nombre personalizado para el archivo
        
    Returns:
        str: URL pública del archivo almacenado
        
    Raises:
        NotFoundError: Si el archivo no existe
        ValidationError: Si el nombre personalizado no es válido
        ProcessingError: Si hay un error al almacenar
    """
    ensure_storage_dir()
    
    if not os.path.exists(file_path):
        raise NotFoundError(f"Archivo no encontrado: {file_path}")
    
    # Determinar nombre de archivo destino
    if custom_filename:
        if not is_valid_filename(custom_filename):
            raise ValidationError(f"Nombre de archivo personalizado inválido: {custom_filename}")
        target_filename = custom_filename
    else:
        # Generar nombre único con la misma extensión
        extension = os.path.splitext(file_path)[1]
        target_filename = f"{uuid.uuid4()}{extension}"
    
    target_path = get_file_path(target_filename)
    
    try:
        # Copiar archivo a almacenamiento
        shutil.copy2(file_path, target_path)
        
        # Crear metadatos (timestamp)
        with open(f"{target_path}.meta", "w") as f:
            f.write(datetime.now().isoformat())
        
        logger.info(f"Archivo almacenado: {target_path}")
        
        # Devolver URL pública
        return get_file_url(target_filename)
    
    except Exception as e:
        logger.error(f"Error almacenando archivo {file_path}: {str(e)}")
        
        # Limpiar archivos parciales en caso de error
        if os.path.exists(target_path):
            safe_delete_file(target_path)
        if os.path.exists(f"{target_path}.meta"):
            safe_delete_file(f"{target_path}.meta")
            
        raise ProcessingError(f"Error almacenando archivo: {str(e)}")

def cleanup_old_files():
    """
    Limpia archivos antiguos del almacenamiento.
    
    Returns:
        tuple: (Archivos eliminados, Bytes liberados)
    """
    try:
        ensure_storage_dir()
        
        files_removed = 0
        bytes_freed = 0
        now = datetime.now()
        
        # Convertir a segundos
        max_age_seconds = settings.MAX_FILE_AGE_HOURS * 3600
        
        for filename in os.listdir(settings.STORAGE_PATH):
            if filename.endswith('.meta'):
                continue  # Saltar archivos de metadatos
                
            file_path = os.path.join(settings.STORAGE_PATH, filename)
            meta_path = f"{file_path}.meta"
            
            file_age = None
            
            # Intentar determinar edad del archivo
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r") as f:
                        created_time = datetime.fromisoformat(f.read().strip())
                        file_age = (now - created_time).total_seconds()
                except:
                    # Si falla, usar mtime
                    file_age = None
            
            if file_age is None:
                # Fallback a mtime
                file_age = now.timestamp() - os.path.getmtime(file_path)
            
            # Si el archivo es antiguo, eliminarlo
            if file_age > max_age_seconds:
                try:
                    file_size = os.path.getsize(file_path)
                    
                    # Eliminar archivo y metadatos
                    os.remove(file_path)
                    if os.path.exists(meta_path):
                        os.remove(meta_path)
                        
                    files_removed += 1
                    bytes_freed += file_size
                    
                    logger.debug(f"Archivo eliminado por antigüedad: {file_path}")
                except Exception as e:
                    logger.error(f"Error eliminando archivo antiguo {file_path}: {str(e)}")
        
        if files_removed > 0:
            logger.info(f"Limpieza: {files_removed} archivos eliminados, {bytes_freed/1024/1024:.2f} MB liberados")
            
        return files_removed, bytes_freed
    
    except Exception as e:
        logger.error(f"Error en cleanup_old_files: {str(e)}")
        return 0, 0
