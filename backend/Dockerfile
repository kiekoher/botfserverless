# Stage 1: Builder
# This stage installs all dependencies into a virtual environment.
FROM python:3.11-slim as builder

WORKDIR /app

# Install poetry and configure it
RUN pip install poetry

# Copy only the files needed for dependency installation
COPY requirements.txt ./

# Install dependencies into a virtual environment
# Using a virtual environment to isolate dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runner
# This stage creates the final, lean image.
FROM python:3.11-slim as runner

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
COPY ./app /app/app

# Activate the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8000

# Run the application with multiple workers for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
