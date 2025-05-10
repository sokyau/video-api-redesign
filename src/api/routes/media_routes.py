# src/api/routes/media_routes.py
from flask import Blueprint, request, jsonify
from src.services.media_service import extract_audio, transcribe_media
from src.api.middlewares.authentication import require_api_key
from src.api.middlewares.request_validator import validate_json
import logging

logger = logging.getLogger(__name__)

# Crear blueprint
media_bp = Blueprint('media', __name__, url_prefix='/api/v1/media')

# Schema para endpoint media_to_mp3
media_to_mp3_schema = {
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "bitrate": {"type": "string", "pattern": "^[0-9]+k$"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["media_url"],
    "additionalProperties": False
}

# Schema para endpoint de transcripción
transcribe_schema = {
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "language": {"type": "string"},
        "output_format": {"type": "string", "enum": ["txt", "srt", "vtt", "json"]},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["media_url"],
    "additionalProperties": False
}

@media_bp.route('/media-to-mp3', methods=['POST'])
@require_api_key
@validate_json(media_to_mp3_schema)
def media_to_mp3_endpoint():
    """
    Extrae audio de archivo multimedia y convierte a MP3
    
    Request:
        - media_url: URL del archivo multimedia
        - bitrate: Bitrate de audio (p.ej., "192k")
        - webhook_url: URL para notificación
        - id: ID de trabajo personalizado opcional
    
    Response:
        - JSON con URL del audio extraído o estado del trabajo
    """
    data = request.get_json()
    
    try:
        job_id = data.get('id')
        
        # Extraer audio
        result = extract_audio(
            media_url=data['media_url'],
            bitrate=data.get('bitrate', '192k'),
            job_id=job_id,
            webhook_url=data.get('webhook_url')
        )
        
        return jsonify({
            "status": "success",
            "result": result,
            "job_id": job_id
        })
    
    except Exception as e:
        logger.exception(f"Error extrayendo audio: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": str(e)
        }), 500

@media_bp.route('/transcribe', methods=['POST'])
@require_api_key
@validate_json(transcribe_schema)
def transcribe_endpoint():
    """
    Transcribe audio de archivo multimedia
    
    Request:
        - media_url: URL del archivo multimedia
        - language: Código de idioma o "auto"
        - output_format: Formato de salida (txt, srt, vtt, json)
        - webhook_url: URL para notificación
        - id: ID de trabajo personalizado opcional
    
    Response:
        - JSON con transcripción o estado del trabajo
    """
    data = request.get_json()
    
    try:
        job_id = data.get('id')
        
        # Transcribir multimedia
        result = transcribe_media(
            media_url=data['media_url'],
            language=data.get('language', 'auto'),
            output_format=data.get('output_format', 'txt'),
            job_id=job_id,
            webhook_url=data.get('webhook_url')
        )
        
        return jsonify({
            "status": "success",
            "result": result,
            "job_id": job_id
        })
    
    except Exception as e:
        logger.exception(f"Error transcribiendo multimedia: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "processing_error",
            "message": str(e)
        }), 500
