# ─────────────────────────────────────────────────────────────────────────────
# CarbonTracker AI — Backend Dockerfile
# Production-grade multi-stage build
# ─────────────────────────────────────────────────────────────────────────────

# Stage 1: Builder — install Python dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Runtime — minimal production image
FROM python:3.12-slim AS runtime

LABEL maintainer="CarbonTracker AI Team"
LABEL version="1.0.0"
LABEL description="CarbonTracker AI Backend — FastAPI Production Server"

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user for security
RUN groupadd --gid 1001 carbontracker \
    && useradd --uid 1001 --gid carbontracker --shell /bin/bash --create-home carbontracker

# Create required directories
RUN mkdir -p /app/static/avatars /app/logs \
    && chown -R carbontracker:carbontracker /app

# Copy application source
COPY --chown=carbontracker:carbontracker app/ ./app/

# Do NOT copy .env files.
# Render injects environment variables securely.

# Switch to non-root user
USER carbontracker

# Expose API port
EXPOSE 8001

# Health check — uses public endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8001}/api/system/status || exit 1

# Download spaCy model at build time (cached in image)
RUN python -m spacy download en_core_web_sm --quiet || true

# Production server command
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001} --workers 2 --log-level info --access-log --proxy-headers --forwarded-allow-ips '*'"]
