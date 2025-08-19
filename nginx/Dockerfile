# Use the official Nginx image from Docker Hub
FROM nginx:stable-alpine

# Remove the default Nginx configuration file
RUN rm /etc/nginx/conf.d/default.conf

# Copy the PRODUCTION configuration file
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf
