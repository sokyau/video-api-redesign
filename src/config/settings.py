import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env si existe
load_dotenv()

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Configuración de API
API_KEY = os.environ.get('API_KEY')
if not API_KEY:
    raise ValueError("La variable de entorno API_KEY es obligatoria")

# Entorno de ejecución
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'production')
DEBUG = ENVIRONMENT.lower() == 'development'

# Configuración de almacenamiento
STORAGE_PATH = os.environ.get('STORAGE_PATH', os.path.join(BASE_DIR, 'storage'))
TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8080/storage')
MAX_FILE_AGE_HOURS = int(os.environ.get('MAX_FILE_AGE_HOURS', 24))

# Configuración de rendimiento
WORKER_PROCESSES = int(os.environ.get('WORKER_PROCESSES', 4))
FFMPEG_THREADS = int(os.environ.get('FFMPEG_THREADS', 4))
MAX_QUEUE_LENGTH = int(os.environ.get('MAX_QUEUE_LENGTH', 100))
MAX_PROCESSING_TIME = int(os.environ.get('MAX_PROCESSING_TIME', 1800))  # 30 minutos
FFMPEG_TIMEOUT = int(os.environ.get('FFMPEG_TIMEOUT', MAX_PROCESSING_TIME))

# Configuración de logs
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Configuración de Whisper para transcripción
WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'base')
WHISPER_TIMEOUT = int(os.environ.get('WHISPER_TIMEOUT', 3600))  # 1 hora

# Configuración de aceleración por GPU
USE_GPU_ACCELERATION = os.environ.get('USE_GPU_ACCELERATION', 'false').lower() == 'true'

# Verificar y crear directorios necesarios
os.makedirs(STORAGE_PATH, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(os.path.join(TEMP_DIR, 'cache'), exist_ok=True)

# Logging config dictionary for use with logging.config.dictConfig
LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': LOG_LEVEL,
            'formatter': 'default',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': LOG_LEVEL,
            'formatter': 'default',
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 5,
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'default',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 10,
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file', 'error_file'],
            'level': LOG_LEVEL,
        },
    },
}
