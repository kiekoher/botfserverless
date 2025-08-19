# Use an official Node.js runtime as a parent image, updated to version 20
FROM node:20-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Install dependencies needed for Puppeteer/whatsapp-web.js
# This is a long list of dependencies required for headless Chrome to run.
RUN apt-get update && apt-get install -y \
    ca-certificates \
    fonts-liberation \
    gconf-service \
    libappindicator1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the application
RUN useradd -ms /bin/bash botuser
USER botuser

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY --chown=botuser:botuser package*.json ./

# Install app dependencies
RUN npm install --only=production

# Copy the rest of the application code
COPY --chown=botuser:botuser . .

# Command to run the application
CMD ["npm", "start"]
