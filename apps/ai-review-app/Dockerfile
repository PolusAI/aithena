FROM python:3.11-slim

# environment variables
ENV AITHENA_LOG_LEVEL="DEBUG"
ENV EXEC_DIR="/opt/executables"
# Work directory defined in the base container
WORKDIR ${EXEC_DIR}

# TOOL_DIR Argument to the Dockerfile
ARG TOOL_DIR="."

COPY $TOOL_DIR ${EXEC_DIR}/${TOOL_DIR}
COPY common ${EXEC_DIR}/common
COPY jobs ${EXEC_DIR}/jobs
COPY services/aithena-services ${EXEC_DIR}/services/aithena-services

# Install the tool
RUN pip3 install "${EXEC_DIR}/${TOOL_DIR}"

EXPOSE 8765

CMD ["solara", "run", "apps/ai-review-app/src/polus/aithena/ai_review_app/main.py", "--host=0.0.0.0", "--production"]