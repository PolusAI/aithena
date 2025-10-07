FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Environment variables
ENV AITHENA_LOG_LEVEL="DEBUG"

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Create a non-root user and switch to it
RUN useradd -m -u 1000 user
USER user

# Set working directory inside user's home
WORKDIR /home/user/app

# Copy project definition and lock file
COPY --chown=user:user ./pyproject.toml ./uv.lock ./
# Copy the README file
COPY --chown=user:user ./README.md ./README.md
# Install dependencies
RUN uv sync

# Copy the rest of the application
COPY --chown=user:user ./src ./src

# Expose the application port
EXPOSE 8000

# Run the application using the CLI
# Environment variables can be passed via docker run -e or docker-compose environment:
# Example: docker run -e POSTGRES_HOST=my-db-host -e POSTGRES_PORT=5433 ...
CMD ["uv", "run", "aithena-services", "serve", "--host", "0.0.0.0", "--port", "8000"]
