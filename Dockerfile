# Etapa de producción: DueloAnimalBot completo
FROM node:18-slim

# Variables
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Dependencias del sistema
RUN apt-get update && \
    apt-get install -y curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Crear usuario no root por seguridad
RUN useradd -ms /bin/bash botuser

# Crear carpetas necesarias
RUN mkdir -p /app/jsonl_output /app/documentos

# Copiar archivos del bot
WORKDIR /app
COPY . .

# Instalar dependencias
RUN npm install

# Cambiar dueño de la app
RUN chown -R botuser:botuser /app

# Usuario seguro
USER botuser

# Comando que ejecuta el watcher embebido
CMD ["node", "auto_ingest.cjs"]
