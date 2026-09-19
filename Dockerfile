# Production Multi-Stage Dockerfile for Google Cloud Run Deployment
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final Runtime Stage
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
