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


# Set the entrypoint
# TODO: Change the entrypoint to the tool entrypoint
ENTRYPOINT ["bash", "-c", "uvicorn polus.aithena.ask_aithena.api.__init__:app --host 0.0.0.0  --port 8000"]
# ENTRYPOINT ["python3", "-m", "polus.aithena.ask_aithena"]
CMD ["--help"]
