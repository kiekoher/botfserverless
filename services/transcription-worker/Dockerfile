# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt ./

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runner
FROM python:3.11-slim as runner

# Crea un directorio para el código de la aplicación
WORKDIR /code

# Copia el entorno virtual del builder
COPY --from=builder /opt/venv /opt/venv

# Copia el código de la aplicación a la carpeta /code/app
COPY ./app /code/app

# Activa el entorno virtual
ENV PATH="/opt/venv/bin:$PATH"

# Añade el directorio /code al PYTHONPATH
ENV PYTHONPATH=/code

# Ejecuta el script como un módulo
CMD ["python", "-m", "app.main"]
