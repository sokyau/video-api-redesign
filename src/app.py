import os
import logging.config
import uuid
from flask import Flask, jsonify, request, g, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import time

from .config import settings
from .api.routes import register_routes
from .api.docs import register_docs

logging.config.dictConfig(settings.LOGGING_CONFIG)
logger = logging.getLogger(__name__)

def register_blueprints(app):
    """Registra todos los blueprints de la API"""
    from .api.routes.video_routes import video_bp
    from .api.routes.media_routes import media_bp
    from .api.routes.system_routes import system_bp
    from .api.routes.ffmpeg_routes import ffmpeg_bp

    app.register_blueprint(video_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(ffmpeg_bp)

    return app

def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    CORS(app)
    
    app.config['STORAGE_PATH'] = settings.STORAGE_PATH
    app.config['DEBUG'] = settings.DEBUG
    
    register_routes(app)
    register_docs(app)

    @app.before_request
    def before_request():
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        g.request_id = request_id
        g.start_time = time.time()
        
        if request.path != '/health':
            logger.info(f"Request {request_id}: {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        response.headers['X-Request-ID'] = g.get('request_id', 'unknown')
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        
        duration = time.time() - g.get('start_time', time.time())
        
        if request.path != '/health':
            logger.info(f"Request {g.get('request_id', 'unknown')} completed in {duration:.3f}s with status {response.status_code}")
        
        return response
    
    @app.route('/')
    def index():
        return jsonify({
            "service": "Video Processing API",
            "status": "operational",
            "version": "1.0.0",
            "documentation": "/api/docs"
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "storage": "ok",
            "ffmpeg": "ok"
        })
    
    @app.route('/storage/<path:filename>')
    def serve_file(filename):
        if '..' in filename or filename.startswith('/'):
            return jsonify({"error": "Acceso no autorizado"}), 403
        
        if not os.path.exists(os.path.join(settings.STORAGE_PATH, filename)):
            return jsonify({"error": "Archivo no encontrado"}), 404
            
        return send_from_directory(settings.STORAGE_PATH, filename)
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception(f"Error no manejado: {str(e)}")
        
        return jsonify({
            "status": "error",
            "message": "Se produjo un error interno del servidor",
            "request_id": g.get('request_id', 'unknown')
        }), 500
    
    logger.info(f"Aplicación inicializada en modo: {settings.ENVIRONMENT}")
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=settings.DEBUG)
