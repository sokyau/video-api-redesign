# src/services/cleanup_service.py
import os
import logging
import time
import shutil
from datetime import datetime, timedelta
from threading import Thread, Event
from src.config import settings
from src.utils.file_utils import format_size

logger = logging.getLogger(__name__)

class CleanupService:
    """Servicio para limpiar archivos antiguos"""
    
    def __init__(self, interval_minutes=60):
        """
        Inicializar servicio de limpieza
        
        Args:
            interval_minutes: Intervalo de limpieza en minutos
        """
        self.interval = interval_minutes * 60  # Convertir a segundos
        self.stop_event = Event()
        self.thread = None
    
    def start(self):
        """Iniciar servicio de limpieza en segundo plano"""
        if self.thread is not None and self.thread.is_alive():
            logger.warning("Servicio de limpieza ya en ejecución")
            return
        
        self.stop_event.clear()
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"Servicio de limpieza iniciado con intervalo de {self.interval/60} minutos")
    
    def stop(self):
        """Detener el servicio de limpieza"""
        if not self.thread:
            logger.warning("Servicio de limpieza no está en ejecución")
            return
        
        logger.info("Deteniendo servicio de limpieza...")
        self.stop_event.set()
        self.thread.join(timeout=30)
        
        if self.thread.is_alive():
            logger.warning("El servicio de limpieza no terminó correctamente")
        else:
            logger.info("Servicio de limpieza detenido")
            self.thread = None
    
    def _run(self):
        """Ejecutar el ciclo de limpieza"""
        logger.info("Ejecutando servicio de limpieza")
        
        while not self.stop_event.is_set():
            try:
                files_removed, bytes_freed = self.cleanup_old_files()
                
                if files_removed > 0:
                    logger.info(f"Limpiados {files_removed} archivos antiguos ({format_size(bytes_freed)})")
                
                # Esperar hasta el próximo intervalo o hasta que se solicite parar
                self.stop_event.wait(self.interval)
                
            except Exception as e:
                logger.exception(f"Error en servicio de limpieza: {str(e)}")
                # Esperar un tiempo menor antes de reintentar
                self.stop_event.wait(60)
    
    def cleanup_old_files(self):
        """
        Limpiar archivos antiguos en almacenamiento y directorios temporales
        
        Returns:
            tuple: (files_removed, bytes_freed)
        """
        total_files_removed = 0
        total_bytes_freed = 0
        
        # Limpiar directorio de almacenamiento
        storage_files, storage_bytes = self._cleanup_directory(
            settings.STORAGE_PATH,
            settings.MAX_FILE_AGE_HOURS
        )
        total_files_removed += storage_files
        total_bytes_freed += storage_bytes
        
        # Limpiar directorio temporal
        temp_files, temp_bytes = self._cleanup_directory(
            settings.TEMP_DIR,
            12  # Tiempo de vida más corto para archivos temporales, p.ej., 12 horas
        )
        total_files_removed += temp_files
        total_bytes_freed += temp_bytes
        
        return total_files_removed, total_bytes_freed
    
    def _cleanup_directory(self, directory, max_age_hours):
        """Limpia archivos antiguos en un directorio específico"""
        if not os.path.isdir(directory):
            logger.warning(f"Directorio de limpieza no existe: {directory}")
            return 0, 0
        
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()
        files_removed = 0
        bytes_freed = 0
        
        for root, _, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                
                # Omitir archivos especiales
                if filename.startswith('.'):
                    continue
                
                try:
                    # Obtener edad del archivo
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    # Si el archivo es lo suficientemente antiguo, eliminarlo
                    if file_age > max_age_seconds:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        
                        # También eliminar archivo .meta si existe
                        meta_path = f"{file_path}.meta"
                        if os.path.exists(meta_path):
                            os.remove(meta_path)
                        
                        files_removed += 1
                        bytes_freed += file_size
                
                except Exception as e:
                    logger.error(f"Error limpiando archivo {file_path}: {str(e)}")
        
        return files_removed, bytes_freed
    
# Crear instancia singleton
cleanup_service = CleanupService()

# Auto-iniciar al importar (puede deshabilitarse)
cleanup_service.start()
