# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install build-essential if any packages need to compile from source
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements.
# We copy both so the layer can be cached, even if only one is used.
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt


# Stage 2: Final production image
FROM python:3.11-slim as runner

# Install ffmpeg, which is a runtime dependency for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Create a non-root user to run the application
RUN useradd --create-home --shell /bin/bash appuser

# Copy application code
COPY --chown=appuser:appuser ./app /code/app

# Activate the virtual environment for all subsequent commands
ENV PATH="/opt/venv/bin:$PATH"

# Set the user to the non-root user
USER appuser

# Set the default command
CMD ["python", "-m", "app.main"]
