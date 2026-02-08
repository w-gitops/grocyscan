# GrocyScan / HomeBot - Multi-stage Dockerfile
# Stage 1: Build Vue/Quasar frontend
# Stage 2: Python backend with built frontend

# ============================================
# Stage 1: Frontend Build
# ============================================
FROM node:20-slim AS frontend-builder

WORKDIR /build

# Copy package files first for better layer caching
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

# Copy frontend source and build
COPY frontend/ ./
RUN NODE_ENV=production npm run build

# ============================================
# Stage 2: Python Backend + Built Frontend
# ============================================
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .
COPY pyproject.toml .

# Copy built frontend from Stage 1
COPY --from=frontend-builder /build/dist ./frontend/dist/

# Create non-root user
RUN useradd -m -u 1000 grocyscan && chown -R grocyscan:grocyscan /app
USER grocyscan

# Expose port
EXPOSE 3334

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3334/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3334"]
