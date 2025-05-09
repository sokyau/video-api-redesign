import functools
import json
from flask import request, jsonify
from jsonschema import validate, ValidationError as JSONSchemaValidationError
import logging

logger = logging.getLogger(__name__)

def validate_json(schema):
    """
    Decorador para validar el payload JSON de una solicitud.
    
    Args:
        schema (dict): Schema JSON para validación.
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar Content-Type
            if request.content_type != 'application/json':
                return jsonify({
                    "status": "error",
                    "error": "invalid_content_type",
                    "message": "El Content-Type debe ser application/json"
                }), 415  # Unsupported Media Type
            
            # Verificar que hay un payload
            if not request.data:
                return jsonify({
                    "status": "error",
                    "error": "empty_payload",
                    "message": "No se proporcionó un payload JSON"
                }), 400
            
            try:
                # Intentar parsear el JSON
                payload = request.get_json()
                
                # Validar contra el schema
                validate(instance=payload, schema=schema)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Error de decodificación JSON: {str(e)}")
                return jsonify({
                    "status": "error",
                    "error": "invalid_json",
                    "message": "El payload no es un JSON válido"
                }), 400
            
            except JSONSchemaValidationError as e:
                logger.warning(f"Error de validación JSON Schema: {str(e)}")
                # Preparar mensaje de error detallado
                error_path = ".".join(str(p) for p in e.path) if e.path else "unknown"
                return jsonify({
                    "status": "error",
                    "error": "validation_error",
                    "message": f"Error de validación en {error_path}: {e.message}",
                    "details": {
                        "path": error_path,
                        "message": e.message
                    }
                }), 400
            
            # Si todo está bien, continuar
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
