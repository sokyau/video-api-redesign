# src/api/routes/jobs_routes.py
from flask import Blueprint, jsonify, request
from src.services.queue_service import get_task_status
from src.api.middlewares.authentication import require_api_key
import logging

logger = logging.getLogger(__name__)

# Crear blueprint
jobs_bp = Blueprint('jobs', __name__, url_prefix='/api/v1/jobs')

@jobs_bp.route('/<job_id>', methods=['GET'])
@require_api_key
def get_job_status(job_id):
    """
    Obtiene estado de un trabajo
    
    Args:
        job_id: ID del trabajo a consultar
    
    Response:
        - JSON con estado del trabajo
    """
    # Obtener información de tarea
    task_info = get_task_status(job_id)
    
    if not task_info:
        return jsonify({
            "status": "error",
            "error": "job_not_found",
            "message": f"Trabajo con ID {job_id} no encontrado"
        }), 404
    
    # Preparar respuesta
    response = {
        "status": "success",
        "job_id": job_id,
        "job_status": {
            "status": task_info["status"],
            "created_at": task_info["created_at"],
            "updated_at": task_info["updated_at"]
        }
    }
    
    # Añadir información adicional según el estado
    if task_info["status"] == "completed":
        response["job_status"]["completed_at"] = task_info.get("completed_at")
        response["job_status"]["result"] = task_info.get("result")
    
    elif task_info["status"] == "failed":
        response["job_status"]["error"] = task_info.get("error")
    
    return jsonify(response)
