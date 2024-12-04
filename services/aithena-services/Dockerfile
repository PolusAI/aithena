FROM python:3.11-slim

# environment variables
ENV AITHENA_LOG_LEVEL="DEBUG"
ENV EXEC_DIR="/opt/executables"
# Work directory defined in the base container
WORKDIR ${EXEC_DIR}

# TOOL_DIR Argument to the Dockerfile
ARG TOOL_DIR="."

# Copy the repository into the container
RUN mkdir aithena
COPY $TOOL_DIR ${EXEC_DIR}/aithena/${TOOL_DIR}
COPY common ${EXEC_DIR}/aithena/common

# Install the tool
RUN pip3 install "${EXEC_DIR}/aithena/${TOOL_DIR}"

EXPOSE 80

CMD ["bash", "-c", "uvicorn aithena_services.api.main:app --host 0.0.0.0 --port 80"]
