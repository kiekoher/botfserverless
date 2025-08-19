# Stage 1: Build the Next.js application
# Use Node.js 20 as required by newer Supabase versions
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application source code
COPY . .

# Declare build arguments that will be passed from docker-compose.yml
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY

# Set them as environment variables FOR THE BUILD PROCESS
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY

# Build the application
RUN npm run build

# Stage 2: Production image - using a standalone Next.js server
# Use the same Node.js version for consistency
FROM node:20-alpine

WORKDIR /app

# --- MEJORA: Instala curl para el healthcheck ---
RUN apk add --no-cache curl

# Copy the output of the build from the builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package.json ./package.json

# Install only the production dependencies.
RUN npm install --only=production

# Expose the port the app runs on
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
