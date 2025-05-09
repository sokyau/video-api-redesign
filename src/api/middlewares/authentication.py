import functools
from flask import request, jsonify
import logging
from ...config import settings

logger = logging.getLogger(__name__)

def require_api_key(f):
    """
    Decorador para autenticación de endpoints mediante API key.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning("Solicitud sin API key")
            return jsonify({
                "status": "error",
                "error": "Se requiere API key",
                "message": "Proporcione una API key válida en el header X-API-Key"
            }), 401
        
        if api_key != settings.API_KEY:
            logger.warning("Solicitud con API key inválida")
            return jsonify({
                "status": "error",
                "error": "API key inválida",
                "message": "La API key proporcionada no es válida"
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function
