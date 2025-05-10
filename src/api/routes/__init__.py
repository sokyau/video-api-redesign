# src/api/routes/__init__.py

def register_routes(app):
    """Registra todas las rutas de la API"""
    from .video_routes import video_bp
    from .media_routes import media_bp
    from .system_routes import system_bp
    
    # Registrar blueprints
    app.register_blueprint(video_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(system_bp)
    
    return app
