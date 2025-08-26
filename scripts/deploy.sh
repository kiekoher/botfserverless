#!/bin/bash
set -euo pipefail

# ==============================================================================
# EVA WHATSAPP GATEWAY DEPLOYMENT SCRIPT (V2 - Immutable Artifacts)
# ==============================================================================
# This script pulls a pre-built Docker image from a registry and deploys it.
# It is designed to be executed by the GitHub Actions workflow.
#
# REQUIREMENTS:
#   - doppler CLI
#   - docker & docker-compose
#
# ENVIRONMENT VARIABLES (provided by CI/CD):
#   - DOPPLER_TOKEN: For logging into Doppler and the container registry.
#   - IMAGE_NAME: The full name of the image to pull (e.g., ghcr.io/owner/repo).
#   - IMAGE_TAG: The specific tag (e.g., commit SHA) of the image to pull.
# ==============================================================================

# --- Helper Functions ---
log() {
    echo
    echo "▶️  $(date +'%Y-%m-%d %H:%M:%S') - $1"
    echo "----------------------------------------------------------------"
}

# --- Pre-flight Checks ---
if ! command -v doppler &> /dev/null || ! command -v docker &> /dev/null; then
    log "ERROR: Docker or Doppler CLI is not installed or not in PATH."
    exit 1
fi

if [ -z "${IMAGE_NAME-}" ] || [ -z "${IMAGE_TAG-}" ]; then
    log "ERROR: IMAGE_NAME and IMAGE_TAG must be set in the environment."
    exit 1
fi

if [ -z "${DOPPLER_TOKEN-}" ]; then
    log "ERROR: DOPPLER_TOKEN must be set for logging into the container registry."
    exit 1
fi

# Ensure Doppler is configured correctly.
if ! doppler whoami &> /dev/null; then
    log "ERROR: Doppler login failed. Ensure DOPPLER_TOKEN is valid."
    exit 1
fi

# --- Deployment Process ---
log "Starting deployment of EVA WhatsApp Gateway..."
log "Image: ${IMAGE_NAME}:${IMAGE_TAG}"

# 1. Log in to GitHub Container Registry
log "Logging in to GitHub Container Registry (ghcr.io)..."
# We use the Doppler service token as the password, which is a supported method for GHCR.
if ! echo "${DOPPLER_TOKEN}" | docker login ghcr.io -u "eva-ci-bot" --password-stdin; then
    log "❌ Docker login to ghcr.io failed."
    exit 1
fi

# 2. Pull the new Docker image from the registry
log "Pulling new image from registry..."
if ! docker pull "${IMAGE_NAME}:${IMAGE_TAG}"; then
    log "❌ Failed to pull Docker image. Check registry and image name/tag."
    exit 1
fi

# 3. Deploy with Docker Compose using the new image
log "Deploying services using docker-compose and Doppler secrets..."
# The `doppler run` command injects secrets into the environment for the container.
# The WHATSAPP_GATEWAY_IMAGE var is passed to docker-compose to specify the image.
export WHATSAPP_GATEWAY_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
if doppler run --project eva --config prd -- docker-compose -f docker-compose.prod.yml up -d; then
    log "✅ Service deployed successfully."
else
    log "❌ Deployment failed. Check the logs from docker-compose."
    exit 1
fi

# 4. Clean up old, unused Docker images
log "Cleaning up old Docker images..."
docker image prune -f

log "🚀 Deployment finished successfully!"
exit 0
