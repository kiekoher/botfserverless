#!/bin/bash
set -e
set -o pipefail

# --- Configuration ---
# This path is the mount point inside the backup container.
BACKUP_DIR="/backups"
# Number of old backups to keep.
KEEP_BACKUPS=7
# (Optional) Healthchecks.io or other monitoring service URL to ping on success.
HEALTHCHECK_URL="" # e.g., "https://hc-ping.com/YOUR_CHECK_UUID"
# (Optional) Cloudflare R2 credentials for off-site backups.
# Ensure rclone is configured on the server with a remote named 'r2'.
R2_REMOTE_NAME="r2"
R2_BUCKET_PATH="eva-backups" # The bucket and folder path, e.g., "my-bucket/eva-backups"

# --- Script Logic ---
echo "---"
echo "Starting backup for project EVA at $(date)"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Define Docker volumes to back up. These must match the volume names in docker-compose.
# The script will look for volumes in the standard Docker directory.
# Note: Project name is derived from the container names (e.g., eva_redis_prod -> eva)
PROJECT_NAME=$(docker ps --format '{{.Names}}' | grep '_redis_prod' | sed 's/_redis_prod//')
if [ -z "$PROJECT_NAME" ]; then
    echo "ERROR: Could not determine project name from running containers. Expected a container like 'eva_redis_prod'."
    exit 1
fi
echo "Detected project name: $PROJECT_NAME"

DOCKER_VOLUMES_PATH="/var/lib/docker/volumes"
VOLUMES_TO_BACKUP=(
  "${PROJECT_NAME}_redis_data"
  "${PROJECT_NAME}_whatsapp_session_prod"
  "${PROJECT_NAME}_traefik_data"
  "${PROJECT_NAME}_prometheus_data"
  "${PROJECT_NAME}_alertmanager_data"
  "${PROJECT_NAME}_grafana_data"
)

# --- Pre-Backup Actions ---
echo "Forcing Redis to save data to disk (BGSAVE)..."
# Send a BGSAVE command to Redis to ensure data is flushed to disk without blocking.
docker exec "${PROJECT_NAME}_redis_prod" redis-cli BGSAVE
echo "Waiting a few seconds for BGSAVE to initiate..."
sleep 5

# --- Create Backup Archive ---
BACKUP_FILENAME="${PROJECT_NAME}_$(date +%Y-%m-%d_%H-%M-%S).tar.gz"
BACKUP_FULL_PATH="$BACKUP_DIR/$BACKUP_FILENAME"

echo "Creating tarball of Docker volumes..."
# Build the list of volume paths to include in the tar command.
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
  exit 1
fi

# Create a compressed tarball of the specified volumes.
if tar --create --gzip --file "$BACKUP_FULL_PATH" "${VOLUME_PATHS[@]}"; then
  echo "Successfully created backup: $BACKUP_FULL_PATH"
else
  echo "ERROR: Failed to create backup tarball."
  exit 1
fi

# --- Off-site Backup (Optional) ---
if command -v rclone &> /dev/null && [ -n "$R2_BUCKET_PATH" ]; then
  echo "Uploading backup to R2 remote '$R2_REMOTE_NAME'..."
  if rclone copyto "$BACKUP_FULL_PATH" "${R2_REMOTE_NAME}:${R2_BUCKET_PATH}/${BACKUP_FILENAME}" --progress; then
    echo "Successfully uploaded backup to R2."
  else
    echo "WARNING: Failed to upload backup to R2. The local backup is still available."
    # Depending on policy, you might want this to be a fatal error (exit 1).
  fi
else
  echo "Skipping off-site backup (rclone not found or R2_BUCKET_PATH not set)."
fi

# --- Clean Up Old Local Backups ---
echo "Cleaning up old local backups (keeping last $KEEP_BACKUPS)..."
# Find and delete backups in the backup directory that are older than the N most recent ones.
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
echo "----------------------------------------------------"
