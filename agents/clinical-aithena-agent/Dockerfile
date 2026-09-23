# Multi-stage Dockerfile for Clinical Aithena API
# Stage 1: Docs builder - Build mkdocs site
FROM python:3.12-slim AS docs-builder

RUN pip install --no-cache-dir mkdocs-material

WORKDIR /docs
COPY mkdocs.yml ./
COPY docs/ ./docs/
RUN mkdocs build --strict

# Stage 2: App builder - Install dependencies
FROM python:3.12-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Copy source code
COPY src/ ./src/

# Install dependencies using uv
# Use --no-dev to skip development dependencies
RUN uv pip install --system --no-cache .

# Stage 3: Runtime - Minimal image with only what's needed
FROM python:3.12-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash apiuser

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Download NLTK data required by the pipeline (punkt_tab tokenizer)
# This is done before switching to non-root user so data goes to a system path.
RUN python -c "import nltk; nltk.download('punkt_tab', download_dir='/usr/local/nltk_data')"

# Copy source code
COPY --chown=apiuser:apiuser src/ ./src/

# Copy built documentation site
COPY --from=docs-builder --chown=apiuser:apiuser /docs/site ./site/

# Switch to non-root user
USER apiuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/apiuser/.local/bin:$PATH" \
    NLTK_DATA="/usr/local/nltk_data"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "polus.aithena.clinical_aithena.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

