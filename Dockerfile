# Etapa de producción: DueloAnimalBot completo
FROM node:18-slim

# Variables de entorno
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Instalar dependencias del sistema para que Puppeteer (de whatsapp-web.js) funcione
RUN apt-get update && apt-get install -y \
    gconf-service \
    libasound2 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
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
    ca-certificates \
    fonts-liberation \
    libappindicator1 \
    libnss3 \
    lsb-release \
    xdg-utils \
    wget \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Crear usuario no root por seguridad
RUN useradd -ms /bin/bash botuser

# Crear y establecer el directorio de trabajo
WORKDIR /app

# Copiar primero los archivos de dependencias para optimizar el cache de Docker
COPY package.json package-lock.json ./

# Instalar todas las dependencias
RUN npm install

# Copiar el resto del código de la aplicación
COPY . .

# Cambiar el dueño de todos los archivos de la app al usuario no root
RUN chown -R botuser:botuser /app

# Cambiar al usuario no root
USER botuser

# El CMD por defecto se definirá en el docker-compose.yml
# Esto es solo un fallback por si se ejecuta sin docker-compose
CMD [ "node", "bot.js" ]
