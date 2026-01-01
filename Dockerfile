# Synth Mind - Production Dockerfile
# Multi-stage build for optimized image size

ARG VERSION=0.1.0-alpha

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM python:3.11-slim as production

ARG VERSION
LABEL org.opencontainers.image.title="Synth Mind" \
      org.opencontainers.image.description="A Psychologically Grounded AI Agent" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.source="https://github.com/synth-mind/synth-mind" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash synth

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=synth:synth . .

# Create necessary directories
RUN mkdir -p /app/state /app/certs && \
    chown -R synth:synth /app/state /app/certs

# Switch to non-root user
USER synth

# Environment variables with defaults
ENV PORT=8080 \
    LOG_LEVEL=INFO \
    LOG_FILE=/app/state/synth.log \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health/live || exit 1

# Default command: Run dashboard server
CMD ["python", "dashboard/run_synth_with_dashboard.py"]

# =============================================================================
# Alternative entry points (use with --entrypoint or docker-compose command:)
# =============================================================================
# CLI only: python run_synth.py
# Dashboard with SSL: python dashboard/server.py --ssl-dev
# With custom port: python dashboard/run_synth_with_dashboard.py --port 9000
