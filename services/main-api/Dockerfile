# Stage 1: Builder
FROM python:3.11-slim as builder

COPY requirements.txt /app/
WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runner
FROM python:3.11-slim as runner

# Crea un directorio para el código de la aplicación
WORKDIR /code

# --- MEJORA: Instala curl Y TAMBIÉN procps (para pgrep) para el healthcheck ---
RUN apt-get update && apt-get install -y curl procps && rm -rf /var/lib/apt/lists/*

# Copia el entorno virtual del builder
COPY --from=builder /opt/venv /opt/venv

# Copia el código de la aplicación a la carpeta /code/app
COPY ./app /code/app

# Activa el entorno virtual
ENV PATH="/opt/venv/bin:$PATH"

# Añade el directorio /code al PYTHONPATH para que Python encuentre el paquete 'app'
ENV PYTHONPATH=/code

# Ejecuta el script como un módulo desde la raíz del código
CMD ["python", "-m", "app.main"]
