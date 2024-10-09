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
COPY . /ask_aithena_dashboard

# Install the tool
RUN pip3 install "${EXEC_DIR}/aithena/${TOOL_DIR}"

EXPOSE 8765

CMD ["solara", "run", "aithena/apps/ask-aithena-app/src/polus/aithena/ask_aithena_app/dashboard.py", "--host=0.0.0.0", "--production"]