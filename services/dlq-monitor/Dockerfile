FROM python:3.11-slim
WORKDIR /app
COPY requirements-prod.txt .
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir -r requirements-prod.txt
ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
RUN useradd -ms /bin/bash appuser
COPY --chown=appuser:appuser ./app /app
USER appuser
CMD ["python", "main.py"]
