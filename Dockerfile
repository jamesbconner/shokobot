# Multi-stage build for ShokoBot
# Stage 1: Builder
FROM python:3.13.9-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Copy source code needed for installation
COPY cli ./cli
COPY services ./services
COPY models ./models
COPY utils ./utils
COPY prompts ./prompts
COPY ui ./ui
COPY README.md ./

# Install the package and its dependencies using pip
# This works with PEP 621 format and respects poetry.lock via pip-compile
RUN pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.13.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 shokobot && \
    mkdir -p /app /data /app/.chroma && \
    chown -R shokobot:shokobot /app /data

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=shokobot:shokobot . .

# Switch to non-root user
USER shokobot

# Create volume mount points
VOLUME ["/data", "/app/.chroma, /resources", "/input"]

# Expose port for web UI
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Default command - use shokobot CLI entry point
CMD ["shokobot", "web", "--port", "7860"]
