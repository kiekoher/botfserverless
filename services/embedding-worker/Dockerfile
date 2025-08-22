# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Create a virtual environment and install dependencies
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt

# Ensure the virtualenv binaries are on PATH
ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Copy the rest of the application's code into the container at /app
COPY ./app /app

# Command to run the application
CMD ["python", "main.py"]
