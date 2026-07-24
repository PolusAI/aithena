FROM ghcr.io/astral-sh/uv:python3.11-bookworm

ENV EXEC_DIR="/opt/executables"

WORKDIR ${EXEC_DIR}

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

COPY jobs/get-openalex/pyproject.toml ${EXEC_DIR}/aithena/jobs/get-openalex/pyproject.toml
COPY jobs/get-openalex/src/ ${EXEC_DIR}/aithena/jobs/get-openalex/src
COPY jobs/get-openalex/uv.lock ${EXEC_DIR}/aithena/jobs/get-openalex/uv.lock
COPY jobs/get-openalex/README.md ${EXEC_DIR}/aithena/jobs/get-openalex/README.md

COPY common ${EXEC_DIR}/aithena/common

# Create data directory for SQLite
RUN mkdir -p ${EXEC_DIR}/data ${EXEC_DIR}/logs
# Install CA certificates
RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates

# Expose API port
EXPOSE 8000

WORKDIR ${EXEC_DIR}/aithena/jobs/get-openalex
RUN uv sync

# Run API
CMD ["uv", "run", "src/polus/aithena/jobs/getopenalex/api/run.py"]
