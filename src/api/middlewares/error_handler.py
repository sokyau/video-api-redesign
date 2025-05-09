import logging
import traceback
import json
from flask import jsonify, request, current_app
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, message, status_code=400, error_code=None, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "api_error"
        self.details = details or {}

class ValidationError(APIError):
    """Error de validación de datos"""
    def __init__(self, message, details=None):
        super().__init__(message=message, status_code=400, error_code="validation_error", details=details)

class NotFoundError(APIError):
    """Recurso no encontrado"""
    def __init__(self, message, details=None):
        super().__init__(message=message, status_code=404, error_code="not_found", details=details)

class ProcessingError(APIError):
    """Error en el procesamiento"""
    def __init__(self, message, details=None):
        super().__init__(message=message, status_code=500, error_code="processing_error", details=details)

def register_error_handlers(app):
    """Registra manejadores de errores para la aplicación"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Maneja errores de API personalizados"""
        response = {
            "status": "error",
            "error": error.error_code,
            "message": error.message
        }
        
        # Añadir detalles si existen y estamos en modo depuración
        if error.details and app.config.get('DEBUG', False):
            response["details"] = error.details
        
        return jsonify(response), error.status_code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Maneja errores 404 Not Found"""
        return jsonify({
            "status": "error",
            "error": "not_found",
            "message": "El recurso solicitado no existe"
        }), 404
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Maneja errores 400 Bad Request"""
        return jsonify({
            "status": "error",
            "error": "bad_request",
            "message": str(error) or "La solicitud es inválida"
        }), 400
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Maneja excepciones no capturadas"""
        # Si es una excepción HTTP de Werkzeug, usar su código de estado
        if isinstance(error, HTTPException):
            return jsonify({
                "status": "error",
                "error": error.name.lower().replace(' ', '_'),
                "message": error.description
            }), error.code
        
        # Generar un ID de error para poder rastrearlo en los logs
        error_id = f"err_{request.path.replace('/', '_')}_{id(error)}"
        
        # Loggear el error completo
        logger.exception(f"Error no manejado [{error_id}]: {str(error)}")
        
        # En producción, mostrar mensaje genérico
        # En desarrollo, incluir más detalles
        if current_app.config.get('DEBUG', False):
            response = {
                "status": "error",
                "error": "server_error",
                "message": str(error),
                "error_id": error_id,
                "traceback": traceback.format_exc()
            }
        else:
            response = {
                "status": "error",
                "error": "server_error",
                "message": "Se produjo un error interno del servidor",
                "error_id": error_id
            }
        
        return jsonify(response), 500
