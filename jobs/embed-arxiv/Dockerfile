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
COPY jobs/oaipmh-client ${EXEC_DIR}/aithena/jobs/oaipmh-client
## --- END: Copy project dependencies ---

# Install the tool
RUN pip3 install "${EXEC_DIR}/aithena/${TOOL_DIR}"

## --- BEGIN: configure the container ---
ENV AITHENA_LOG_LEVEL="DEBUG"
ENV ARXIV_LIST_RECORDS_DIR="/inputs/downloads/export.arxiv.org/ListRecords"
ENTRYPOINT ["python3", "-m", "polus.aithena.document_services.arxiv_abstract_ingestion"]
CMD ["--help"]
