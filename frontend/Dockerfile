# Stage 1: Build the Next.js application
# Use Node.js 20 as required by newer Supabase versions
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Use npm ci for deterministic builds
RUN npm ci

# Copy the rest of the application source code
COPY . .

# Declare build arguments that will be passed from docker-compose.yml
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY

# Set them as environment variables FOR THE BUILD PROCESS
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY

# Build the application
# The `output: 'standalone'` in next.config.js will create a .next/standalone folder
RUN npm run build

# Stage 2: Production image - using the standalone output
# Use the same Node.js version for consistency
FROM node:20-alpine

WORKDIR /app

# --- MEJORA IMPLEMENTADA ---
# Se instala wget, que es la herramienta que usa el healthcheck en docker-compose.prod.yml
RUN apk add --no-cache wget

# Copy the standalone output from the builder stage.
# This includes a minimal server.js, node_modules, and required .next files.
COPY --from=builder /app/.next/standalone ./

# Expose the port the app runs on
EXPOSE 3000

# Set the user to a non-root user for better security
USER node

# Start the application using the standalone server
CMD ["node", "server.js"]

