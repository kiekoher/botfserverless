# Etapa de producción: DueloAnimalBot completo

FROM node:18-slim

# Variables
ENV DEBIAN_FRONTEND=noninteractive
ENV OLLAMA_MODELS=/models
ENV LANG=C.UTF-8

# Dependencias del sistema
RUN apt update && \
    apt install -y curl unzip git jq build-essential && \
    rm -rf /var/lib/apt/lists/*

# Crear usuario no root por seguridad
RUN useradd -ms /bin/bash botuser

# Crear carpetas necesarias
RUN mkdir -p /app/jsonl_output /app/documentos /models

# Copiar archivos del bot
WORKDIR /app
COPY . .

# Instalar dependencias (reemplazamos npm ci por install)
RUN npm install

# Descargar modelo Mistral GGUF
RUN curl -L -o /models/mistral-7b-instruct-v0.1.Q4_K_M.gguf https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf

# Cambiar dueño de la app
RUN chown -R botuser:botuser /app

# Usuario seguro
USER botuser

# Comando que ejecuta el watcher embebido
CMD ["node", "auto_ingest.cjs"]
