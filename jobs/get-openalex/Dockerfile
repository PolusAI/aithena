FROM python:3.11-slim

# Work directory defined in the base container
ENV EXEC_DIR="/opt/executables"
WORKDIR ${EXEC_DIR}

# TOOL_DIR Argument to the Dockerfile
ARG TOOL_DIR="."

# Copy the repository into the container
RUN mkdir aithena
COPY $TOOL_DIR ${EXEC_DIR}/aithena/${TOOL_DIR}

# Tool dependencies

## --- BEGIN: Copy project dependencies  ---
COPY common ${EXEC_DIR}/aithena/common
## --- END: Copy project dependencies ---

# Install the tool
RUN pip3 install "${EXEC_DIR}/aithena/${TOOL_DIR}"

## --- BEGIN: configure the container ---
ENV AITHENA_LOG_LEVEL="DEBUG"
ENTRYPOINT ["get-openalex"]
## --- END: configure the container ---