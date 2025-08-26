#!/bin/bash
set -euo pipefail # Exit on error, undefined variable, or pipe failure

# ==============================================================================
# EVA WHATSAPP GATEWAY BACKUP SCRIPT
# ==============================================================================
# This script creates a compressed archive of a Docker volume and uploads it
# to a Cloudflare R2 bucket. It is designed to be run as a cron job.
#
# REQUIREMENTS:
#   - sudo (to access Docker volumes)
#   - aws-cli (v2) installed and configured for Cloudflare R2.
#   - curl
#
# ENVIRONMENT VARIABLES:
#   - R2_BUCKET_NAME: The name of your R2 bucket.
#   - R2_ACCOUNT_ID: Your Cloudflare Account ID.
#   - AWS_ACCESS_KEY_ID: Your R2 Access Key ID.
#   - AWS_SECRET_ACCESS_KEY: Your R2 Secret Access Key.
#   - BACKUP_HEARTBEAT_URL: (Optional) A URL to ping upon completion/failure.
# ==============================================================================

# --- Configuration ---
readonly VOLUME_NAME="whatsapp_session_prod"
readonly DOCKER_ROOT_PATH="/var/lib/docker/volumes"

# --- Helper Functions ---
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

ping_heartbeat() {
    if [ -z "${BACKUP_HEARTBEAT_URL-}" ]; then
        return 0 # Do nothing if URL is not set
    fi

    local url="$BACKUP_HEARTBEAT_URL"
    # Append /fail for failure pings, if the service supports it.
    if [ "${1-}" == "fail" ]; then
        url="$url/fail"
    fi

    log "Pinging heartbeat URL..."
    if ! curl -fsS --retry 3 "$url" > /dev/null; then
        log "WARNING: Failed to ping heartbeat URL."
    fi
}

# --- Pre-flight Checks ---
if ! command -v aws &> /dev/null || ! command -v curl &> /dev/null; then
    log "ERROR: Required commands (aws-cli, curl) are not installed."
    ping_heartbeat "fail"
    exit 1
fi

if [ -z "${R2_BUCKET_NAME-}" ] || [ -z "${R2_ACCOUNT_ID-}" ] || [ -z "${AWS_ACCESS_KEY_ID-}" ] || [ -z "${AWS_SECRET_ACCESS_KEY-}" ]; then
    log "ERROR: Required R2 environment variables are not set."
    ping_heartbeat "fail"
    exit 1
fi

# --- Backup Process ---
log "Starting backup for volume: $VOLUME_NAME"

readonly VOLUME_PATH="$DOCKER_ROOT_PATH/$VOLUME_NAME/_data"
readonly BACKUP_FILENAME="whatsapp_session_backup_$(date +'%Y%m%d_%H%M%S').tar.gz"
readonly BACKUP_TMP_PATH="/tmp/$BACKUP_FILENAME"
readonly R2_ENDPOINT="https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com"
readonly R2_S3_URI="s3://$R2_BUCKET_NAME/whatsapp-gateway-backups/$BACKUP_FILENAME"

if [ ! -d "$VOLUME_PATH" ]; then
    log "ERROR: Docker volume path not found at $VOLUME_PATH."
    ping_heartbeat "fail"
    exit 1
fi

log "Creating archive: $BACKUP_TMP_PATH"
if ! sudo tar -czf "$BACKUP_TMP_PATH" -C "$VOLUME_PATH" .; then
    log "ERROR: Failed to create tarball."
    ping_heartbeat "fail"
    exit 1
fi

log "Uploading archive to $R2_S3_URI"
if ! aws s3 cp "$BACKUP_TMP_PATH" "$R2_S3_URI" --endpoint-url "$R2_ENDPOINT"; then
    log "ERROR: Failed to upload to R2."
    sudo rm -f "$BACKUP_TMP_PATH" # Clean up even if upload fails
    ping_heartbeat "fail"
    exit 1
fi

log "Cleaning up local archive file."
sudo rm -f "$BACKUP_TMP_PATH"

log "Backup completed successfully!"
ping_heartbeat "ok"
exit 0
