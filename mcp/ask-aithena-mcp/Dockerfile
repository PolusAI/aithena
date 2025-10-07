# Build stage
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS builder

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Build the package
RUN uv build

# Runtime stage
FROM python:3.13-alpine AS runtime

# Install uv in runtime for package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Copy built wheel and install it
COPY --from=builder /app/dist/*.whl ./
RUN uv pip install --system --no-cache *.whl && \
    rm *.whl

# Copy source code (needed for the module structure)
COPY --from=builder /app/src/ ./src/
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE 3283

# Set the entry point
CMD ["python", "-m", "polus.aithena.ask_aithena_mcp.server"]
