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

# Copy the virtual environment from the builder
COPY --from=builder /opt/venv /opt/venv

RUN useradd -ms /bin/bash appuser

# Copy the application code to the /code/app folder
COPY --chown=appuser:appuser ./app /code/app

# Activate the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Add the /code directory to PYTHONPATH
ENV PYTHONPATH=/code

USER appuser

# Execute the script as a module
CMD ["python", "-m", "app.main"]
