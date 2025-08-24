# Stage 1: Build the Next.js application
# Use Node.js 20 as required by newer Supabase versions
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Use npm ci for deterministic builds (includes dev deps for build)
RUN npm ci

# Copy the rest of the application source code
COPY . .

# Build the application
# The `output: 'standalone'` in next.config.js will create a .next/standalone folder
# Note: Build args are passed in via the docker-compose file, no need to declare them here again
# if they are only used during the build.
RUN npm run build

# Stage 2: Production image - using the standalone output
FROM node:20-alpine

WORKDIR /app

# Install curl, which is used by the healthcheck in docker-compose.prod.yml
RUN apk add --no-cache curl

# Copy the standalone output from the builder stage.
# This includes a minimal server.js, node_modules, and required .next files.
COPY --from=builder /app/.next/standalone ./
# Copy the public folder for static assets like images
COPY --from=builder /app/public ./public

# Expose the port the app runs on
EXPOSE 3000

# Set the user to a non-root user for better security
USER node

# Start the application using the standalone server
CMD ["node", "server.js"]
