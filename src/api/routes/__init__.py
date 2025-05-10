# src/api/routes/__init__.py

def register_routes(app):
    """Registra todas las rutas de la API"""
    try:
        from .video_routes import video_bp
        app.register_blueprint(video_bp)
    except ImportError as e:
        print(f"Error importing video_routes: {e}")
    
    try:
        from .media_routes import media_bp
        app.register_blueprint(media_bp)
    except ImportError as e:
        print(f"Error importing media_routes: {e}")
    
    try:
        from .system_routes import system_bp
        app.register_blueprint(system_bp)
    except ImportError as e:
        print(f"Error importing system_routes: {e}")
    
    try:
        from .ffmpeg_routes import ffmpeg_bp
        app.register_blueprint(ffmpeg_bp)
    except ImportError as e:
        print(f"Error importing ffmpeg_routes: {e}")
    
    return app
