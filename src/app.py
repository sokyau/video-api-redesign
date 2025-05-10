import os
import logging.config
import uuid
from flask import Flask, jsonify, request, g, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import time

# Importar configuración
from src.api.routes import register_routes
from src.api.docs import register_docs
from .config import settings

# Configurar logging
logging.config.dictConfig(settings.LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# src/app.py - Añadir después de crear la app

def register_blueprints(app):
 """Registra todos los blueprints de la API"""
 from src.api.routes.video_routes import video_bp
 # Importar otros blueprints a medida que se creen

 # Registrar blueprints
 app.register_blueprint(video_bp)
 # Registrar otros blueprints

 return app
def create_app():
    """Crea y configura la aplicación Flask"""
    # Crear aplicación Flask
    app = Flask(__name__)
    
    # Configurar para trabajar detrás de proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Configurar CORS
    CORS(app)
    
    # Configurar variables globales de la aplicación
    app.config['STORAGE_PATH'] = settings.STORAGE_PATH
    app.config['DEBUG'] = settings.DEBUG
    
    register_routes(app)
    register_docs(app)

    # Registrar before/after request handlers
    @app.before_request
    def before_request():
        """Setup request context and logging"""
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        g.request_id = request_id
        g.start_time = time.time()
        
        # Skip logging for health checks to reduce noise
        if request.path != '/health':
            logger.info(f"Request {request_id}: {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        """Add response headers and log completion"""
        # Add request ID to response
        response.headers['X-Request-ID'] = g.get('request_id', 'unknown')
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Calculate duration
        duration = time.time() - g.get('start_time', time.time())
        
        # Skip logging for health checks
        if request.path != '/health':
            logger.info(f"Request {g.get('request_id', 'unknown')} completed in {duration:.3f}s with status {response.status_code}")
        
        return response
    
    # Registrar rutas básicas
    @app.route('/')
    def index():
        """Endpoint de información de la API"""
        return jsonify({
            "service": "Video Processing API",
            "status": "operational",
            "version": "1.0.0",
            "documentation": "/api/docs"
        })
    
    @app.route('/health')
    def health():
        """Endpoint para health check"""
        return jsonify({
            "status": "healthy",
            "storage": "ok",
            "ffmpeg": "ok"
        })
    
    @app.route('/storage/<path:filename>')
    def serve_file(filename):
        """Sirve archivos desde el directorio de almacenamiento"""
        # Prevenir path traversal
        if '..' in filename or filename.startswith('/'):
            return jsonify({"error": "Acceso no autorizado"}), 403
        
        if not os.path.exists(os.path.join(settings.STORAGE_PATH, filename)):
            return jsonify({"error": "Archivo no encontrado"}), 404
            
        return send_from_directory(settings.STORAGE_PATH, filename)
    
    # Registrar módulos API
    # Aquí importaremos y registraremos los blueprints posteriormente
    # from .api.routes import register_routes
    # register_routes(app)
    
    # Manejador genérico de errores
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Manejador global de excepciones"""
        logger.exception(f"Error no manejado: {str(e)}")
        
        return jsonify({
            "status": "error",
            "message": "Se produjo un error interno del servidor",
            "request_id": g.get('request_id', 'unknown')
        }), 500
    
    logger.info(f"Aplicación inicializada en modo: {settings.ENVIRONMENT}")
    return app

# Crear la instancia de la aplicación
app = create_app()

if __name__ == '__main__':
    # Solo para desarrollo
    app.run(host='0.0.0.0', port=8080, debug=settings.DEBUG)

