# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt requirements-prod.txt ./
# Install development requirements first to run tests/quality checks if needed in CI
RUN pip install --no-cache-dir -r requirements.txt
# Then install/overwrite with production requirements to keep the layer clean
RUN pip install --no-cache-dir -r requirements-prod.txt


# Stage 2: Final production image
FROM python:3.11-slim as runner

WORKDIR /code

# Install only curl, which is needed for the healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Create a non-root user to run the application
RUN useradd --create-home --shell /bin/bash appuser

# Copy application code
COPY --chown=appuser:appuser ./app /code/app

# Copy and set permissions for the entrypoint script
COPY --chown=appuser:appuser ./entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

# Activate the virtual environment for all subsequent commands
ENV PATH="/opt/venv/bin:$PATH"

# Set the user to the non-root user
USER appuser

# Set the entrypoint
ENTRYPOINT ["/code/entrypoint.sh"]

# The default command is now defined in the entrypoint script itself
# or can be passed by docker-compose
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
