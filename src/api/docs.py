from flask import jsonify
from flask_swagger_ui import get_swaggerui_blueprint

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
        "/api/v1/video/concatenate": {
            "post": {
                "tags": ["Video"],
                "summary": "Concatenar videos",
                "description": "Concatena múltiples videos en uno solo",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["video_urls"],
                                "properties": {
                                    "video_urls": {
                                        "type": "array",
                                        "items": {
                                            "type": "string",
                                            "format": "uri"
                                        },
                                        "description": "Lista de URLs de videos"
                                    },
                                    "webhook_url": {
                                        "type": "string",
                                        "format": "uri",
                                        "description": "URL para webhook de notificación"
                                    },
                                    "id": {
                                        "type": "string",
                                        "description": "ID personalizado"
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
                    }
                }
            }
        },
        "/api/v1/video/animated-text": {
            "post": {
                "tags": ["Video"],
                "summary": "Añadir texto animado",
                "description": "Añade texto animado a un video",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["video_url", "text"],
                                "properties": {
                                    "video_url": {
                                        "type": "string",
                                        "format": "uri",
                                        "description": "URL del video"
                                    },
                                    "text": {
                                        "type": "string",
                                        "description": "Texto a animar"
                                    },
                                    "animation": {
                                        "type": "string",
                                        "enum": ["fade", "slide", "zoom", "typewriter", "bounce"],
                                        "description": "Tipo de animación"
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
                    }
                }
            }
        },
        "/api/v1/ffmpeg/compose": {
            "post": {
                "tags": ["FFmpeg"],
                "summary": "Composición FFmpeg",
                "description": "Realiza una composición avanzada con FFmpeg",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["inputs", "filter_complex"],
                                "properties": {
                                    "inputs": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "url": {
                                                    "type": "string",
                                                    "format": "uri"
                                                },
                                                "options": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "string"
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "filter_complex": {
                                        "type": "string"
                                    },
                                    "output_options": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        }
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
                    }
                }
            }
        }
    }

def register_docs(app):
    """
    Registra la documentación de la API en la aplicación Flask.
    """
    # Configurar ruta para obtener especificación OpenAPI
    @app.route('/api/docs/openapi.json')
    def get_openapi_spec():
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Video Processing API",
                "description": "API para procesamiento de video optimizada para creación de contenido.",
                "version": "1.0.0"
            },
            "servers": [
                {
                    "url": "/",
                    "description": "Servidor actual"
                }
            ],
            "tags": [
                {
                    "name": "Video",
                    "description": "Operaciones relacionadas con videos"
                },
                {
                    "name": "Media",
                    "description": "Operaciones relacionadas con archivos multimedia"
                },
                {
                    "name": "FFmpeg",
                    "description": "Operaciones avanzadas con FFmpeg"
                },
                {
                    "name": "System",
                    "description": "Operaciones del sistema"
                }
            ],
            "paths": get_api_paths(),
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
            ]
        }
        return jsonify(openapi_spec)
    
    # Configurar Swagger UI
    swagger_ui = get_swaggerui_blueprint(
        '/api/docs',
        '/api/docs/openapi.json',
        config={
            'app_name': "Video Processing API",
            'deepLinking': True,
            'displayOperationId': False,
            'displayRequestDuration': True,
            'docExpansion': "list",
            'showExtensions': True,
            'tagsSorter': "alpha"
        }
    )
    
    # Registrar blueprint de Swagger UI
    app.register_blueprint(swagger_ui)
    
    return app
