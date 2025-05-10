# src/api/routes/ffmpeg_routes.py

from flask import Blueprint, request, jsonify
from ..middlewares.authentication import require_api_key
from ..middlewares.request_validator import validate_json
from ...services.ffmpeg_service import run_ffmpeg_command, compose_ffmpeg
import logging

logger = logging.getLogger(__name__)

# Crear blueprint
ffmpeg_bp = Blueprint('ffmpeg', __name__, url_prefix='/api/v1/ffmpeg')

# Schema para validación de ffmpeg_compose
ffmpeg_compose_schema = {
    "type": "object",
    "properties": {
        "inputs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "format": "uri"},
                    "options": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["url"]
            },
            "minItems": 1
        },
        "filter_complex": {"type": "string"},
        "output_options": {
            "type": "array",
            "items": {"type": "string"}
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["inputs", "filter_complex"],
    "additionalProperties": False
}

@ffmpeg_bp.route('/compose', methods=['POST'])
@require_api_key
@validate_json(ffmpeg_compose_schema)
def ffmpeg_compose():
    """
    Composición avanzada con FFmpeg.
    
    Request:
        - inputs: Lista de entradas (URLs y opciones)
        - filter_complex: Filtro complejo de FFmpeg
        - output_options: Opciones para la salida
        - webhook_url: URL para webhook de notificación (opcional)
        - id: ID personalizado (opcional)
    
    Response:
        - JSON con URL del archivo procesado o estado del trabajo
    """
    data = request.get_json()
    
    try:
        job_id = data.get('id')
        
        # Procesar composición FFmpeg
        result = compose_ffmpeg(
            inputs=data['inputs'],
            filter_complex=data['filter_complex'],
            output_options=data.get('output_options', []),
            job_id=job_id,
            webhook_url=data.get('webhook_url')
        )
        
        return jsonify({
            "status": "success",
            "result": result,
            "job_id": job_id
        })
        
    except Exception as e:
        logger.exception(f"Error en composición FFmpeg: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": str(e)
        }), 500
