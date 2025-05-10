# src/api/routes/system_routes.py
from flask import Blueprint, jsonify, request
from src.services.cleanup_service import cleanup_service
from src.api.middlewares.authentication import require_api_key
import logging
import os
import platform
import time
import psutil
from src.config import settings

logger = logging.getLogger(__name__)

# Crear blueprint
system_bp = Blueprint('system', __name__, url_prefix='/api/v1/system')

@system_bp.route('/health', methods=['GET'])
def health():
    """
    Comprueba salud del sistema
    
    Response:
        - JSON con estado de salud
    """
    return jsonify({
        "status": "healthy",
        "storage": "ok",
        "ffmpeg": "ok"
    })

@system_bp.route('/version', methods=['GET'])
def version():
    """
    Obtiene información de versión
    
    Response:
        - JSON con información de versión
    """
    return jsonify({
        "version": "1.0.0",
        "api_version": "v1",
        "build_date": "2023-05-01",  # Actualizar con fecha de build real
        "python_version": platform.python_version(),
        "platform": platform.system()
    })

@system_bp.route('/status', methods=['GET'])
@require_api_key
def status():
    """
    Obtiene información de estado del sistema
    
    Response:
        - JSON con estado del sistema
    """
    # Obtener uso de disco
    disk_usage = cleanup_service.get_disk_usage()
    
    # Obtener uso de memoria
    mem = psutil.virtual_memory()
    
    # Obtener uptime
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    
    # Obtener uso de CPU
    cpu_percent = psutil.cpu_percent(interval=0.5)
    
    # Formatear uptime
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_formatted = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
    
    return jsonify({
        "status": "operational",
        "disk": {
            "total": disk_usage["total"],
            "used": disk_usage["used"],
            "free": disk_usage["free"],
            "percent": disk_usage["percent_used"],
            "total_formatted": disk_usage["total_formatted"],
            "used_formatted": disk_usage["used_formatted"],
            "free_formatted": disk_usage["free_formatted"]
        },
        "memory": {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
            "total_formatted": format_size(mem.total),
            "available_formatted": format_size(mem.available),
            "used_formatted": format_size(mem.used)
        },
        "cpu": {
            "percent": cpu_percent,
            "cores": psutil.cpu_count()
        },
        "uptime": {
            "seconds": uptime_seconds,
            "formatted": uptime_formatted
        }
    })

@system_bp.route('/cleanup', methods=['POST'])
@require_api_key
def cleanup():
    """
    Ejecuta limpieza de archivos manualmente
    
    Response:
        - JSON con resultados de limpieza
    """
    try:
        files_removed, bytes_freed = cleanup_service.run_now()
        
        return jsonify({
            "status": "success",
            "files_removed": files_removed,
            "bytes_freed": bytes_freed,
            "bytes_freed_formatted": format_size(bytes_freed),
            "timestamp": time.time()
        })
    except Exception as e:
        logger.exception(f"Error ejecutando limpieza manual: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "cleanup_failed",
            "message": str(e)
        }), 500

def format_size(size_bytes):
    """Formatea tamaño en bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
