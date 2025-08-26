#!/bin/bash
set -e
set -o pipefail

# --- Configuration ---
COMPOSE_FILE="/app/compose.yml"
BACKUP_DIR="/backups"
KEEP_BACKUPS=7
HEALTHCHECK_URL="${HEALTHCHECK_URL}" # Pass through from compose env
R2_REMOTE_NAME="${R2_REMOTE_NAME:-r2}"
R2_BUCKET_PATH="${R2_BUCKET_PATH}" # Pass through from compose env

# Services with volumes that need to be stopped for a safe backup
SERVICES_TO_STOP=(
  "redis"
  "whatsapp-gateway"
  "traefik"
  "prometheus"
  "alertmanager"
  "grafana"
)

# --- Script Logic ---
echo "---"
echo "Starting backup for project ${COMPOSE_PROJECT_NAME} at $(date)"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Ensure services are restarted even if the script fails
function cleanup {
  echo "---"
  echo "Restarting services..."
  docker-compose -f "$COMPOSE_FILE" up -d "${SERVICES_TO_STOP[@]}"
  echo "Services restarted."
  echo "---"
}
trap cleanup EXIT

# --- Pre-Backup Actions ---
echo "Stopping services with persistent volumes: ${SERVICES_TO_STOP[*]}..."
docker-compose -f "$COMPOSE_FILE" stop "${SERVICES_TO_STOP[@]}"
echo "Services stopped."

# --- Create Backup Archive ---
# Note: The project name is automatically used by docker-compose to name volumes.
PROJECT_NAME=${COMPOSE_PROJECT_NAME:-eva} # Default to 'eva' if not set
VOLUMES_TO_BACKUP=(
  "${PROJECT_NAME}_redis_data"
  "${PROJECT_NAME}_whatsapp_session_prod"
  "${PROJECT_NAME}_traefik_data"
  "${PROJECT_NAME}_prometheus_data"
  "${PROJECT_NAME}_alertmanager_data"
  "${PROJECT_NAME}_grafana_data"
)

DOCKER_VOLUMES_PATH="/var/lib/docker/volumes"
BACKUP_FILENAME="${PROJECT_NAME}_$(date +%Y-%m-%d_%H-%M-%S).tar.gz"
BACKUP_FULL_PATH="$BACKUP_DIR/$BACKUP_FILENAME"

echo "Creating tarball of Docker volumes..."
VOLUME_PATHS=()
for vol in "${VOLUMES_TO_BACKUP[@]}"; do
  if docker volume inspect "$vol" &> /dev/null; then
    # It's critical to use the _data subdirectory within the volume path
    VOLUME_PATHS+=("--directory=${DOCKER_VOLUMES_PATH}/${vol}" "_data")
  else
    echo "WARNING: Volume '$vol' not found. Skipping."
  fi
done

if [ ${#VOLUME_PATHS[@]} -eq 0 ]; then
  echo "ERROR: No volumes found to back up. Aborting."
  # The trap will still run to restart services
  exit 1
fi

if tar --create --gzip --file "$BACKUP_FULL_PATH" "${VOLUME_PATHS[@]}"; then
  echo "Successfully created backup: $BACKUP_FULL_PATH"
else
  echo "ERROR: Failed to create backup tarball."
  # The trap will still run to restart services
  exit 1
fi

# --- Off-site Backup (Optional) ---
if command -v rclone &> /dev/null && [ -n "$R2_BUCKET_PATH" ]; then
  echo "Uploading backup to R2 remote '$R2_REMOTE_NAME'..."
  if rclone copyto "$BACKUP_FULL_PATH" "${R2_REMOTE_NAME}:${R2_BUCKET_PATH}/${BACKUP_FILENAME}" --progress; then
    echo "Successfully uploaded backup to R2."
  else
    echo "WARNING: Failed to upload backup to R2. The local backup is still available."
  fi
else
  echo "Skipping off-site backup (rclone not found or R2_BUCKET_PATH not set)."
fi

# --- Clean Up Old Local Backups ---
echo "Cleaning up old local backups (keeping last $KEEP_BACKUPS)..."
ls -1t "$BACKUP_DIR" | grep ".tar.gz" | tail -n +$(($KEEP_BACKUPS + 1)) | while read -r old_backup; do
  echo "Deleting old backup: $old_backup"
  rm -- "$BACKUP_DIR/$old_backup"
done

# --- Ping Healthcheck URL (Optional) ---
if [ -n "$HEALTHCHECK_URL" ]; then
  echo "Pinging healthcheck URL..."
  curl -fsS -m 10 --retry 5 "$HEALTHCHECK_URL" > /dev/null || echo "WARNING: Failed to ping healthcheck URL."
fi

echo "Backup process completed successfully at $(date)."
# The 'trap cleanup EXIT' will handle restarting the services automatically.
