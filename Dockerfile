# Usar imagen base oficial de Python
FROM python:3.10-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias (incluye FFmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY src/ /app/src/
COPY scripts/ /app/scripts/
COPY tests/ /app/tests/
COPY .env.example /app/.env.example
COPY README.md /app/
COPY wsgi.py /app/

# Crear directorios necesarios con permisos adecuados
RUN mkdir -p /app/storage /app/logs \
    && chmod -R 755 /app/storage /app/logs

# Establecer variable de entorno para Python
ENV PYTHONUNBUFFERED=1
ENV WORKER_PROCESSES=4

# Exponer el puerto que usará la aplicación
EXPOSE 8000

# Comando para iniciar la aplicación con Gunicorn
CMD gunicorn wsgi:app --bind 0.0.0.0:8000 --workers ${WORKER_PROCESSES} --timeout 300
