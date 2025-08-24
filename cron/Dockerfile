# Use Alpine as a lightweight base image
FROM alpine:3.18

# Install necessary packages:
# - dcron: the cron daemon
# - docker-cli: to interact with the Docker engine on the host
# - rclone: for optional off-site backups
RUN apk add --no-cache dcron docker-cli rclone

# Create a directory for the app scripts
WORKDIR /app

# Copy the backup script from the root directory into the container
COPY ../backup.sh .
# Copy the crontab file into the system directory for cron
COPY eva_crontab /etc/crontabs/root

# Make the backup script executable
RUN chmod +x /app/backup.sh

# Set the entrypoint to run the cron daemon in the foreground
CMD ["crond", "-f", "-d", "8"]
