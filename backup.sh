#!/bin/bash
set -e

# --- Configuración ---
# Directorio donde se guardarán los backups temporalmente
BACKUP_DIR="/tmp/eva_backups"
# Nombre del proyecto de Docker Compose (el nombre del directorio del proyecto)
# Este prefijo se usa en los nombres de los volúmenes. Cámbialo si es necesario.
PROJECT_NAME="eva"
# Ruta al archivo docker-compose.prod.yml
DOCKER_COMPOSE_FILE="$(pwd)/docker-compose.prod.yml"
# Configuración para subida a Cloudflare R2 (opcional)
R2_BUCKET_NAME="your-r2-bucket-for-backups" # CAMBIAR: El nombre de tu bucket de R2
R2_ENDPOINT_URL="your-r2-endpoint-url" # CAMBIAR: El endpoint de tu R2

# --- Script ---
echo "Iniciando proceso de backup..."
mkdir -p $BACKUP_DIR
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="eva_volumes_backup_$TIMESTAMP.tar.gz"
BACKUP_FULL_PATH="$BACKUP_DIR/$BACKUP_FILENAME"

# Volúmenes a respaldar
REDIS_VOLUME="${PROJECT_NAME}_redis_data"
WHATSAPP_VOLUME="${PROJECT_NAME}_whatsapp_session_prod"

# Verificar que el archivo de compose existe
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "Error: El archivo docker-compose.prod.yml no se encuentra en $DOCKER_COMPOSE_FILE"
    exit 1
fi

echo "Deteniendo los servicios con estado: whatsapp-gateway y redis..."
docker-compose -f $DOCKER_COMPOSE_FILE stop whatsapp-gateway redis

echo "Creando backup comprimido de los volúmenes..."
# Usamos 'docker volume inspect' para obtener la ruta real de los volúmenes en el host
REDIS_PATH=$(docker volume inspect --format '{{ .Mountpoint }}' $REDIS_VOLUME)
WHATSAPP_PATH=$(docker volume inspect --format '{{ .Mountpoint }}' $WHATSAPP_VOLUME)

tar -czf $BACKUP_FULL_PATH -C $REDIS_PATH . -C $WHATSAPP_PATH .

echo "Backup creado exitosamente en: $BACKUP_FULL_PATH"

echo "Reiniciando los servicios..."
docker-compose -f $DOCKER_COMPOSE_FILE start whatsapp-gateway redis

echo "Proceso de backup local completado."

# --- Subida a Cloudflare R2 (Opcional) ---
# Descomenta las siguientes líneas y configura las variables de arriba
# y las credenciales de AWS/R2 en tu entorno para habilitar la subida.
# echo "Intentando subir el backup a Cloudflare R2..."
# export AWS_ACCESS_KEY_ID="YOUR_R2_ACCESS_KEY_ID"
# export AWS_SECRET_ACCESS_KEY="YOUR_R2_SECRET_ACCESS_KEY"
# aws s3 cp $BACKUP_FULL_PATH s3://$R2_BUCKET_NAME/ --endpoint-url $R2_ENDPOINT_URL
# echo "Subida completada."

# Limpieza de backups locales antiguos (ej. mantener los últimos 7)
echo "Limpiando backups locales antiguos..."
find $BACKUP_DIR -name "eva_volumes_backup_*.tar.gz" -type f -mtime +7 -delete
echo "Limpieza completada."

echo "¡Proceso de backup finalizado con éxito!"
