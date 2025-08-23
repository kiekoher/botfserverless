# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements-prod.txt ./
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements-prod.txt

# Stage 2: Runner
FROM python:3.11-slim as runner

WORKDIR /code

# --- MEJORA IMPLEMENTADA ---
# Se instalan las dependencias necesarias para el healthcheck basado en `nc`.
RUN apt-get update && apt-get install -y curl procps netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copia el entorno virtual del builder
COPY --from=builder /opt/venv /opt/venv

RUN useradd -ms /bin/bash appuser

# Copia el código de la aplicación a la carpeta /code/app
COPY --chown=appuser:appuser ./app /code/app

# Activa el entorno virtual
ENV PATH="/opt/venv/bin:$PATH"

# Añade el directorio /code al PYTHONPATH para que Python encuentre el paquete 'app'
ENV PYTHONPATH=/code

USER appuser

# Ejecuta el script como un módulo desde la raíz del código
CMD ["python", "-m", "app.main"]

