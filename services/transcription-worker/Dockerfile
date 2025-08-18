# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt ./

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runner
FROM python:3.11-slim as runner

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY ./app /app/app

ENV PATH="/opt/venv/bin:$PATH"

CMD ["python", "app/main.py"]
