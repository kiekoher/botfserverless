#!/bin/bash
set -euo pipefail

# ==============================================================================
# EVA WHATSAPP GATEWAY DEPLOYMENT SCRIPT
# ==============================================================================
# This script automates the deployment of the WhatsApp Gateway service on a
# production server. It should be executed by the GitHub Actions workflow.
#
# REQUIREMENTS:
#   - git
#   - doppler CLI
#   - docker & docker-compose
#   - npm
# ==============================================================================

# --- Helper Functions ---
log() {
    echo
    echo "▶️  $(date +'%Y-%m-%d %H:%M:%S') - $1"
    echo "----------------------------------------------------------------"
}

# --- Pre-flight Checks ---
if ! command -v doppler &> /dev/null; then
    log "ERROR: Doppler CLI is not installed or not in PATH."
    exit 1
fi

# Ensure Doppler is logged in. The CI/CD token should be set in the environment.
if ! doppler whoami &> /dev/null; then
    log "ERROR: Doppler login failed. Ensure DOPPLER_TOKEN is set and valid."
    exit 1
fi

# --- Deployment Process ---
log "Starting deployment of EVA WhatsApp Gateway..."

# 1. Navigate to the project directory
# The script assumes it's being run from the project root directory.
# The GitHub Action should ensure it's in the correct location.

# 2. Pull latest changes from the main branch
log "Pulling latest code from 'main' branch..."
git checkout main # Ensure we are on the main branch
git pull origin main

# 3. Install/update Node.js dependencies
log "Installing/updating npm dependencies for the gateway..."
pushd services/whatsapp-gateway > /dev/null
npm install --production --omit=dev
popd > /dev/null # Go back to root

# 4. Deploy with Docker Compose and Doppler
log "Deploying services using docker-compose and Doppler secrets..."
# The `doppler run` command injects secrets into the environment.
# The `--` separates doppler's flags from the command to be executed.
# `up -d --build` will rebuild the image if the Dockerfile changed and restart the container.
if doppler run -- docker-compose -f docker-compose.prod.yml up -d --build; then
    log "✅ Service deployed successfully."
else
    log "❌ Deployment failed. Check the logs from docker-compose."
    exit 1
fi

# 5. Optional: Clean up dangling Docker images to save space
log "Cleaning up old Docker images..."
docker image prune -f

log "🚀 Deployment finished successfully!"
exit 0
