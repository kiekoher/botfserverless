FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt
ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
COPY ./app /app
CMD ["python", "main.py"]
