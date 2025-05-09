8. 📚 Documentación
README.md
markdown# Video Processing API

API para procesamiento de video optimizada para creación de contenido.

## 📋 Características

- Procesamiento de video con FFmpeg
- Superposición de memes en videos
- Añadir subtítulos a videos
- Concatenación de videos
- Añadir texto animado a videos
- Conversión de imágenes a videos
- Extracción de audio de videos
- Transcripción de audio
- Sistema de manejo de tareas en cola

## 🚀 Inicio Rápido

### Prerrequisitos

- Docker y Docker Compose
- O alternativamente: Python 3.10+, FFmpeg y dependencias

### Instalación con Docker

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/video-api.git
   cd video-api

Configurar variables de entorno:
bashcp .env.example .env
# Editar .env con tus configuraciones

Construir y ejecutar con Docker Compose:
bashdocker-compose up -d

Verificar que la API está funcionando:
bashcurl http://localhost:8080/health


Instalación Manual

Clonar el repositorio:
bashgit clone https://github.com/tu-usuario/video-api.git
cd video-api

Instalar dependencias del sistema:
bashsudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg

Crear y activar entorno virtual:
bashpython3 -m venv venv
source venv/bin/activate

Instalar dependencias de Python:
bashpip install -r requirements.txt

Configurar variables de entorno:
bashcp .env.example .env
# Editar .env con tus configuraciones

Ejecutar la aplicación:
bashpython -m src.app


🛠️ Uso de la API
Autenticación
Todas las solicitudes a la API deben incluir la cabecera X-API-Key con la clave API configurada.
Ejemplos de Uso
Añadir Subtítulos a un Video
bashcurl -X POST http://localhost:8080/api/v1/video/caption \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tu_api_key" \
  -d '{
    "video_url": "https://ejemplo.com/video.mp4",
    "subtitles_url": "https://ejemplo.com/subtitulos.srt",
    "font": "Arial",
    "font_size": 24,
    "font_color": "white",
    "background": true,
    "position": "bottom"
  }'
Superponer Meme en Video
bashcurl -X POST http://localhost:8080/api/v1/video/meme-overlay \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tu_api_key" \
  -d '{
    "video_url": "https://ejemplo.com/video.mp4",
    "meme_url": "https://ejemplo.com/meme.png",
    "position": "bottom_right",
    "scale": 0.3
  }'
📖 Documentación Completa
Para obtener información detallada sobre todos los endpoints disponibles, consulta la documentación completa en la siguiente URL cuando el servidor esté en ejecución:
http://localhost:8080/api/docs
🧪 Pruebas
Para ejecutar las pruebas:
bash# En el directorio principal con el entorno virtual activado
pytest
Para ejecutar pruebas con cobertura:
bashpytest --cov=src
🔄 CI/CD
Este proyecto utiliza GitHub Actions para integración continua. Cada commit y pull request activa:

Ejecución de pruebas
Análisis de código con flake8
Construcción de imagen Docker

🚢 Despliegue en Producción
Con Docker (Recomendado)

Asegúrate de tener Docker y Docker Compose instalados en tu servidor
Clona el repositorio y configura el archivo .env
Ejecuta docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

Configuración de Nginx y SSL
Para configurar Nginx como proxy inverso con SSL:

Configura el archivo de sitio de Nginx:
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /storage/ {
        alias /ruta/al/proyecto/storage/;
        expires 6h;
    }
}

Obtén certificados SSL con Certbot:
bashcertbot --nginx -d tu-dominio.com

Reinicia Nginx:
bashsudo systemctl restart nginx


📈 Monitoreo
La API proporciona los siguientes endpoints para monitoreo:

/health - Estado de salud de la API
/metrics - Métricas detalladas del sistema (requiere autenticación)

🔧 Solución de Problemas
Si encuentras problemas:

Verifica los logs:
bashdocker-compose logs -f

Verifica el estado de salud:
bashcurl http://localhost:8080/health

Problemas comunes:

Error 401: Verifica la API key
Error 413: El archivo es demasiado grande
Error 500: Revisa los logs para más detalles



🤝 Contribuciones
¡Las contribuciones son bienvenidas! Por favor, sigue estos pasos:

Fork el repositorio
Crea una rama (git checkout -b feature/amazing-feature)
Realiza tus cambios
Ejecuta las pruebas (pytest)
Haz commit de tus cambios (git commit -m 'Add amazing feature')
Haz push a la rama (git push origin feature/amazing-feature)
Abre un Pull Request

📄 Licencia
Este proyecto está licenciado bajo [tu licencia] - consulta el archivo LICENSE.md para más detalles.

## 9. 🚢 Despliegue en VPS

### Pasos para el despliegue en Ubuntu 22.04

1. **Conectarse al VPS**
   ```bash
   ssh usuario@tu-ip-vps

Actualizar el sistema
bashsudo apt update
sudo apt upgrade -y

Instalar Docker y Docker Compose
bash# Instalar dependencias
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Añadir clave GPG de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Añadir repositorio de Docker
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Actualizar e instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Añadir usuario actual al grupo docker para no necesitar sudo
sudo usermod -aG docker $USER
# Aplicar cambio de grupo (requiere reconectar sesión SSH)
newgrp docker

Instalar Nginx y Certbot
bashsudo apt install -y nginx certbot python3-certbot-nginx

Clonar el repositorio
bash# Crear directorio para la aplicación
mkdir -p ~/apps
cd ~/apps

# Clonar repositorio
git clone https://github.com/tu-usuario/video-api.git
cd video-api

Configurar variables de entorno
bashcp .env.example .env
# Editar archivo .env con editor como nano o vim
nano .env
Configuración mínima recomendada en .env:
API_KEY=tu_api_key_segura
BASE_URL=https://tu-dominio.com/storage
ENVIRONMENT=production
WORKER_PROCESSES=4
FFMPEG_THREADS=4
MAX_FILE_AGE_HOURS=24

Crear directorios necesarios
bashmkdir -p storage logs
# Asegurarse de que tienen permisos adecuados
chmod -R 755 storage logs

Configurar Nginx
bash# Crear archivo de configuración del sitio
sudo nano /etc/nginx/sites-available/video-api.conf
Contenido del archivo:
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts más largos para procesamiento de videos
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }

    location /storage/ {
        alias /home/usuario/apps/video-api/storage/;
        expires 24h;
        add_header Cache-Control "public, max-age=86400";
    }
    
    # Configuración para archivos grandes
    client_max_body_size 1G;
}
Activar la configuración:
bashsudo ln -s /etc/nginx/sites-available/video-api.conf /etc/nginx/sites-enabled/
sudo nginx -t  # Verificar configuración
sudo systemctl restart nginx

Obtener certificado SSL
bashsudo certbot --nginx -d tu-dominio.com

Construir y levantar contenedores Docker
bashcd ~/apps/video-api
docker-compose up -d --build

Verificar que la aplicación está funcionando
bashcurl http://localhost:8080/health

Configurar respaldo automático (opcional)
bash# Crear script de respaldo
nano ~/backup-video-api.sh
Contenido del script:
bash#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR=/home/usuario/backups
APP_DIR=/home/usuario/apps/video-api

# Crear directorio de respaldos si no existe
mkdir -p $BACKUP_DIR

# Respaldar .env y directorios importantes
tar -czf $BACKUP_DIR/video-api_config_$TIMESTAMP.tar.gz $APP_DIR/.env

# Respaldar datos de almacenamiento (no incluir archivos temporales)
find $APP_DIR/storage -type f -not -path "*/\.*" -mtime -7 | tar -czf $BACKUP_DIR/video-api_storage_$TIMESTAMP.tar.gz -T -

# Limpiar respaldos antiguos (mantener últimos 7 días)
find $BACKUP_DIR -type f -name "video-api_*" -mtime +7 -delete
Hacer ejecutable y configurar cron:
bashchmod +x ~/backup-video-api.sh
crontab -e
Añadir la línea:
0 3 * * * /home/usuario/backup-video-api.sh

Configurar monitoreo (opcional)
bash# Crear script simple
nano ~/monitor-video-api.sh
Contenido del script:
bash#!/bin/bash
HEALTH_CHECK=$(curl -s http://localhost:8080/health)

if [[ $HEALTH_CHECK != *"healthy"* ]]; then
    echo "¡ALERTA! Video API no está funcionando correctamente. Reiniciando..."
    cd /home/usuario/apps/video-api
    docker-compose restart
    # Enviar notificación
    curl -X POST -H "Content-Type: application/json" -d '{"text":"Video API reiniciada en el servidor"}' https://tu-webhook-slack-o-telegram
fi
Hacer ejecutable y configurar cron:
bashchmod +x ~/monitor-video-api.sh
crontab -e
Añadir la línea:
*/10 * * * * /home/usuario/monitor-video-api.sh

Configurar logs rotativos
bashsudo nano /etc/logrotate.d/video-api
Contenido:
/home/usuario/apps/video-api/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 usuario usuario
}

Crear script de actualización
bashnano ~/update-video-api.sh
Contenido:
bash#!/bin/bash
set -e

APP_DIR=/home/usuario/apps/video-api

echo "Actualizando Video API..."
cd $APP_DIR

# Guardar .env actual
cp .env .env.backup

# Actualizar desde git
git pull

# Restaurar .env
cp .env.backup .env

# Reconstruir y reiniciar
docker-compose down
docker-compose up -d --build

echo "¡Actualización completada!"
Hacer ejecutable:
bashchmod +x ~/update-video-api.sh


Solución de problemas comunes
Estructura de código inconsistente: La nueva API tiene una estructura clara con separación de responsabilidades entre rutas, servicios y utilidades.
Manejo de errores deficiente: La API anterior carecía de un sistema consistente de manejo de errores. La nueva implementación incluye:

Jerarquía clara de excepciones personalizadas (APIError, ValidationError, ProcessingError, etc.)
Captura y logeo centralizado de errores
Respuestas HTTP consistentes y bien estructuradas
Inclusión de ID de error para facilitar el rastreo en logs


Validación de entrada insuficiente: Anteriormente, la validación de entrada era inconsistente o inexistente. Ahora:

Usamos JSON Schema para validar todas las solicitudes
Hay validaciones adicionales para parámetros críticos (URLs, nombres de archivo, etc.)
Se proporcionan mensajes de error detallados y útiles


Limpieza deficiente de archivos temporales: La API anterior acumulaba archivos temporales:

Ahora tenemos bloques try-finally para garantizar la limpieza incluso en caso de errores
Servicio dedicado de limpieza periódica de archivos antiguos
Sistema de monitoreo del espacio disponible


Problemas de seguridad: Hemos reforzado la seguridad:

Validación estricta de URLs para prevenir SSRF
Verificación de tamaño de archivos antes de procesarlos
Sanitización de nombres de archivo para prevenir ataques de path traversal
Control de acceso consistente mediante API Key


Falta de escalabilidad: La nueva arquitectura es más escalable:

Sistema de cola de tareas para gestionar procesos intensivos
Capacidad para configurar número de workers según recursos disponibles
Optimización del uso de recursos para FFmpeg
Posibilidad de escalar horizontalmente con múltiples instancias


Documentación insuficiente: Hemos mejorado enormemente la documentación:

README detallado con ejemplos de uso
Comentarios en el código para explicar lógica compleja
Documentación de API con Swagger/OpenAPI
Guías de solución de problemas comunes


Manejo subóptimo de FFmpeg: Hemos mejorado cómo interactuamos con FFmpeg:

Mejor construcción y validación de comandos
Control de recursos (threads, timeout)
Detección y manejo adecuado de errores específicos de FFmpeg
Optimización para diferentes tipos de operaciones de video



Mantenimiento y Expansión
Para mantener y expandir la API en el futuro:

Añadir nuevos endpoints:

Crear archivo en src/api/routes/ para definir rutas
Implementar lógica de servicio en src/services/
Añadir validaciones adecuadas
Actualizar documentación
Escribir pruebas unitarias y de integración


Actualizar dependencias:
bash# Con entorno virtual activado
pip list --outdated
pip install --upgrade <paquete>
# Actualizar requirements.txt
pip freeze > requirements.txt

Monitoreo continuo:

Revisar logs periódicamente (/logs)
Monitorear uso de recursos (CPU, memoria, disco)
Verificar tiempos de procesamiento para identificar cuellos de botella


Respaldos:

Mantener respaldos regulares de la configuración
Respaldar archivos importantes en almacenamiento externo
Documentar cualquier cambio significativo



Script de instalación completo
Para facilitar la instalación, aquí tienes un script completo que puedes ejecutar en tu VPS:
bash#!/bin/bash
set -e  # Detener en caso de error

# Colores para hacer la salida más legible
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Instalador de Video API ===${NC}"

# Obtener configuración del usuario
read -p "Introduce el dominio para la API (ej: api.example.com): " DOMAIN
read -p "Introduce tu dirección de email (para Let's Encrypt): " EMAIL
read -s -p "Crea una API key segura: " API_KEY
echo "" # Nueva línea después de la entrada oculta

# Configurar variables
APP_DIR=~/apps/video-api
NGINX_CONF=/etc/nginx/sites-available/video-api.conf

echo -e "${GREEN}=== Actualizando sistema ===${NC}"
sudo apt update && sudo apt upgrade -y

echo -e "${GREEN}=== Instalando dependencias ===${NC}"
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common git nginx certbot python3-certbot-nginx

echo -e "${GREEN}=== Instalando Docker ===${NC}"
# Añadir repositorio de Docker si no está ya
if [ ! -f /etc/apt/sources.list.d/docker.list ]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
  sudo apt update
fi

# Instalar Docker y Docker Compose
sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Añadir usuario actual al grupo docker
sudo usermod -aG docker $USER
newgrp docker

echo -e "${GREEN}=== Creando estructura del proyecto ===${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

# Clonar repositorio (reemplaza con tu repositorio real)
echo -e "${YELLOW}Clonando repositorio...${NC}"
git clone https://github.com/tu-usuario/video-api.git .

# Crear directorios necesarios
mkdir -p storage logs
chmod -R 755 storage logs

# Configurar .env
echo -e "${GREEN}=== Configurando variables de entorno ===${NC}"
cat > .env << EOF
# Configuración de seguridad
API_KEY=$API_KEY

# Configuración del servidor
API_PORT=8080
ENVIRONMENT=production

# Configuración de almacenamiento
STORAGE_PATH=$APP_DIR/storage
BASE_URL=https://$DOMAIN/storage
MAX_FILE_AGE_HOURS=24

# Configuración de rendimiento
WORKER_PROCESSES=4
FFMPEG_THREADS=4
MAX_QUEUE_LENGTH=100
MAX_PROCESSING_TIME=1800

# Configuración de logs
LOG_LEVEL=INFO
ERROR_RETENTION_DAYS=30

# Opciones para GPU
USE_GPU_ACCELERATION=false
EOF

echo -e "${GREEN}=== Configurando Nginx ===${NC}"
# Crear configuración de Nginx
sudo tee $NGINX_CONF > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts más largos para procesamiento de videos
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }

    location /storage/ {
        alias $APP_DIR/storage/;
        expires 24h;
        add_header Cache-Control "public, max-age=86400";
    }
    
    # Configuración para archivos grandes
    client_max_body_size 1G;
}
EOF

# Activar configuración
sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo -e "${GREEN}=== Configurando SSL con Certbot ===${NC}"
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL

echo -e "${GREEN}=== Iniciando la aplicación con Docker ===${NC}"
docker-compose up -d --build

echo -e "${GREEN}=== Configurando scripts de mantenimiento ===${NC}"
# Script de monitoreo
cat > ~/monitor-video-api.sh << 'EOF'
#!/bin/bash
HEALTH_CHECK=$(curl -s http://localhost:8080/health)

if [[ $HEALTH_CHECK != *"healthy"* ]]; then
    echo "¡ALERTA! Video API no está funcionando correctamente. Reiniciando..."
    cd $HOME/apps/video-api
    docker-compose restart
fi
EOF
chmod +x ~/monitor-video-api.sh

# Script de respaldo
cat > ~/backup-video-api.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR=$HOME/backups
APP_DIR=$HOME/apps/video-api

# Crear directorio de respaldos
mkdir -p $BACKUP_DIR

# Respaldar configuración
tar -czf $BACKUP_DIR/video-api_config_$TIMESTAMP.tar.gz $APP_DIR/.env

# Respaldar datos recientes
find $APP_DIR/storage -type f -not -path "*/\.*" -mtime -7 | tar -czf $BACKUP_DIR/video-api_storage_$TIMESTAMP.tar.gz -T -

# Limpiar respaldos antiguos
find $BACKUP_DIR -type f -name "video-api_*" -mtime +7 -delete
EOF
chmod +x ~/backup-video-api.sh

# Configurar cron
(crontab -l 2>/dev/null || echo "") | { cat; echo "*/10 * * * * $HOME/monitor-video-api.sh > /dev/null 2>&1"; } | crontab -
(crontab -l 2>/dev/null) | { cat; echo "0 3 * * * $HOME/backup-video-api.sh > /dev/null 2>&1"; } | crontab -

echo -e "${GREEN}=== Verificando la instalación ===${NC}"
sleep 5
HEALTH_CHECK=$(curl -s http://localhost:8080/health)
if [[ $HEALTH_CHECK == *"healthy"* ]]; then
    echo -e "${GREEN}✅ ¡La API está funcionando correctamente!${NC}"
else
    echo -e "${RED}❌ La API no está respondiendo correctamente. Revisa los logs:${NC}"
    docker-compose logs
fi

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}     ¡Instalación de Video API completada!          ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "URL de la API: ${YELLOW}https://$DOMAIN${NC}"
echo -e "API Key: ${YELLOW}$API_KEY${NC}"
echo -e "Directorio de la aplicación: ${YELLOW}$APP_DIR${NC}"
echo -e ""
echo -e "Para verificar los logs: ${YELLOW}docker-compose logs -f${NC}"
echo -e "Para reiniciar la API: ${YELLOW}docker-compose restart${NC}"
echo -e "Para detener la API: ${YELLOW}docker-compose down${NC}"
echo -e ""
echo -e "${GREEN}¡Gracias por usar Video API!${NC}"
Conclusión
He diseñado una API de procesamiento de video bien estructurada, robusta y escalable que corrige todos los problemas de la implementación anterior. La nueva arquitectura proporciona:

Modularidad: Componentes bien separados que facilitan el mantenimiento y la extensión.
Robustez: Manejo adecuado de errores, validación y excepciones.
Seguridad: Validación exhaustiva de entradas y protección contra ataques comunes.
Rendimiento: Uso optimizado de recursos y sistema de cola para procesamiento eficiente.
Documentación: Documentación completa para usuarios y desarrolladores.
Facilidad de despliegue: Configuración Docker lista para producción.

Este diseño ha sido pensado para un entorno VPS con Ubuntu 22.04, siguiendo las mejores prácticas actuales de desarrollo y despliegue. La arquitectura permite una fácil expansión para añadir nuevas funcionalidades según sea necesario.
