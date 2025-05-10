# src/api/docs.py
from flask import Blueprint, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint
import os
from src.config import settings

# Crear el blueprint para documentación
swagger_bp = Blueprint('swagger', __name__)

# Configuración de Swagger UI
SWAGGER_URL = '/api/docs'
API_URL = '/api/spec'

# Crear blueprint de Swagger UI
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Video Processing API",
        'docExpansion': 'list'
    }
)

# Endpoint para especificación OpenAPI
@swagger_bp.route('/api/spec')
def swagger_spec():
    """
    Proporciona la especificación OpenAPI
    """
    swagger_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Video Processing API",
            "description": "API para procesamiento de video",
            "version": "1.0.0",
            "contact": {
                "name": "API Support",
                "email": "support@example.com"
            }
        },
        "servers": [
            {
                "url": "/",
                "description": "Local server"
            }
        ],
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            }
        },
        "security": [
            {
                "ApiKeyAuth": []
            }
        ],
        "paths": get_api_paths()
    }
    
    return jsonify(swagger_spec)

def get_api_paths():
    """
    Obtiene información de rutas de la API
    """
    return {
        "/api/v1/video/caption": {
            "post": {
                "tags": ["Video"],
                "summary": "Añadir subtítulos a video",
                "description": "Añade subtítulos a un video desde un archivo SRT o VTT",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["video_url", "subtitles_url"],
                                "properties": {
                                    "video_url": {
                                        "type": "string",
                                        "format": "uri",
                                        "description": "URL del video"
                                    },
                                    "subtitles_url": {
                                        "type": "string",
                                        "format": "uri",
                                        "description": "URL del archivo de subtítulos"
                                    },
                                    "font": {
                                        "type": "string",
                                        "description": "Nombre de la fuente"
                                    },
                                    "font_size": {
                                        "type": "integer",
                                        "description": "Tamaño de la fuente"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Éxito",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "result": {"type": "string"},
                                        "job_id": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Datos de entrada inválidos"
                    },
                    "401": {
                        "description": "No autorizado"
                    }
                }
            }
        },
        # Aquí añadir más rutas...
    }

def register_docs(app):
    """
    Registra blueprint de documentación en la app
    """
    app.register_blueprint(swagger_bp)
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
