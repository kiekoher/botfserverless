# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Final production image
FROM python:3.11-slim as runner

WORKDIR /code

# Install any OS-level packages needed by the application or healthcheck
# In this case, nothing extra is needed for the default redis-ping healthcheck

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
