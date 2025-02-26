FROM python:3.11-slim

# Environment variables
ENV AITHENA_LOG_LEVEL="DEBUG"
ENV EXEC_DIR="/opt/executables"
WORKDIR ${EXEC_DIR}


# Copy the required directories
COPY common ${EXEC_DIR}/aithena/common
COPY services/aithena-services ${EXEC_DIR}/aithena/services/aithena-services

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Git and other dependencies in a single RUN command for efficiency
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install the tool using pip
RUN pip3 install "${EXEC_DIR}/aithena/services/aithena-services"

# Expose the application port
EXPOSE 8000

# Run the application
CMD ["bash", "-c", "uvicorn aithena_services.api.main:app --host 0.0.0.0 --port 8000"]