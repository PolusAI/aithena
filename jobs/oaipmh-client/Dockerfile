FROM python:3.11-slim

# environment variables
ENV AITHENA_LOG_LEVEL="DEBUG"
ENV EXEC_DIR="/opt/executables"
# Work directory defined in the base container
WORKDIR ${EXEC_DIR}

# TODO: Change the tool_dir to the tool directory
ENV TOOL_DIR="document-services/oai-pmh-client"

# Copy the repository into the container
RUN mkdir aithena
COPY . ${EXEC_DIR}/aithena

# Install the tool
RUN pip3 install "${EXEC_DIR}/aithena/${TOOL_DIR}" --no-cache-dir

# Set the entrypoint
# TODO: Change the entrypoint to the tool entrypoint
ENTRYPOINT ["python3", "-m", "polus.aithena.oai_pmh_client"]
CMD ["--help"]
