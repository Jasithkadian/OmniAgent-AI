FROM python:3.11-slim AS builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies
COPY --from=builder /usr/local/lib /usr/local/lib
COPY --from=builder /usr/local/bin /usr/local/bin

# Add a non-root user
RUN addgroup --system appgroup && adduser --system --group appuser

# Copy application code
COPY backend/ /app/backend/
COPY agents/ /app/agents/
COPY rag/ /app/rag/

# Set PYTHONPATH so absolute imports work (e.g., from app.core...)
ENV PYTHONPATH=/app/backend:/app

# Create directories for persistent storage (Chroma, Uploads) and set permissions
RUN mkdir -p /app/backend/var/uploads /app/backend/var/chroma && chown -R appuser:appgroup /app/backend/var

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

WORKDIR /app/backend

# The default command runs the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]