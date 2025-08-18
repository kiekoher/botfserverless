# Stage 1: Build the Next.js application
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
# Using --only=production can reduce image size if devDependencies are not needed for the build
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Production image - using a standalone Next.js server
FROM node:18-alpine

WORKDIR /app

# Copy the output of the build from the builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

# It is not recommended to copy the whole node_modules folder.
# Instead, we should install only the production dependencies.
# This ensures a smaller and more secure final image.
RUN npm install --only=production

# Expose the port the app runs on
EXPOSE 3000

# Set the user to a non-root user for security
# RUN addgroup -S nextjs && adduser -S nextjs -G nextjs
# USER nextjs

# Start the application
CMD ["npm", "start"]
