FROM python:3.11-slim

ARG PORT=8765
ARG TOOL_DIR="."

# environment variables
ENV AITHENA_LOG_LEVEL="DEBUG"
ENV EXEC_DIR="/opt/executables"
# Work directory defined in the base container
WORKDIR ${EXEC_DIR}/${TOOL_DIR}

RUN apt update && \
    apt upgrade -y

COPY ${TOOL_DIR}/src ${EXEC_DIR}/${TOOL_DIR}/src   
COPY ${TOOL_DIR}/pyproject.toml ${EXEC_DIR}/${TOOL_DIR}/pyproject.toml
COPY ${TOOL_DIR}/README.md ${EXEC_DIR}/${TOOL_DIR}/README.md

RUN pip3 install ${EXEC_DIR}/${TOOL_DIR} --no-cache-dir

EXPOSE $PORT

ENV PORT=$PORT

CMD ["solara", "run", "src/polus/aithena/chat-app/dashboard.py", "--host=0.0.0.0", "--production"]