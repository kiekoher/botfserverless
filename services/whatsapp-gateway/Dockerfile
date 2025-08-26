# Stage 1: Build
FROM node:20-slim as builder

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install all dependencies for reproducible builds
RUN npm ci

# Copy the rest of the application source code
COPY . .

# Stage 2: Production
FROM node:20-slim as runner

# Set environment for production
ENV NODE_ENV=production
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Install only production system dependencies needed for Puppeteer.
# This list is kept from the original Dockerfile as it's specific to whatsapp-web.js.
RUN apt-get update && apt-get install -y \
    ca-certificates fonts-liberation libappindicator1 libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 \
    libgbm1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 \
    libnspr4 libnss3 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 \
    libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 \
    libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 lsb-release \
    wget xdg-utils \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd -ms /bin/bash botuser
USER botuser

WORKDIR /app

# Copy only necessary files from the builder stage
COPY --from=builder --chown=botuser:botuser /app/node_modules ./node_modules
COPY --from=builder --chown=botuser:botuser /app/package.json ./package.json
COPY --from=builder --chown=botuser:botuser /app/package-lock.json ./package-lock.json
COPY --from=builder --chown=botuser:botuser /app/bot.js ./bot.js
COPY --from=builder --chown=botuser:botuser /app/keys.js ./keys.js

# Command to run the application
CMD ["npm", "start"]
