FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Environment variables
ENV AITHENA_LOG_LEVEL="DEBUG"

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install git and clean up apt cache to keep the image lean
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# pyproject.toml expects embeddings at a specific absolute path, so copy it there as root
COPY embeddings /home/embeddings

# Create a non-root user for security
RUN useradd -m -u 1000 user
USER user

# Set working directory inside user's home for proper permissions
WORKDIR /home/user/app

# Copy only the dependency definitions first to leverage Docker cache
COPY --chown=user:user agents/ask-aithena-agent/pyproject.toml agents/ask-aithena-agent/uv.lock ./
COPY --chown=user:user agents/ask-aithena-agent/README.md ./

# Install dependencies
RUN uv sync

# Now copy the rest of the application code
COPY --chown=user:user agents/ask-aithena-agent/src ./src

# Expose the application port
EXPOSE 8000

# Use CMD for flexibility, consistent with the other service
CMD ["uv", "run", "ask-aithena", "serve", "--log-level", "DEBUG", "--host", "0.0.0.0", "--port", "8000"]
