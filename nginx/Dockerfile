# Use the official Nginx image from Docker Hub
FROM nginx:stable-alpine

# Remove the default Nginx configuration file
RUN rm /etc/nginx/conf.d/default.conf

# --- MEJORA IMPLEMENTADA ---
# Se corrige el nombre del archivo para que coincida con el que existe en el repositorio.
COPY nginx.prod.conf.template /etc/nginx/conf.d/default.conf

