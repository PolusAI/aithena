FROM python:3.11-slim

ARG PORT=8765

RUN apt update && \
    apt upgrade -y

COPY src /aithena_agent_chat/src
COPY pyproject.toml /aithena_agent_chat/pyproject.toml
COPY README.md /aithena_agent_chat/README.md

RUN pip3 install /aithena_agent_chat --no-cache-dir
WORKDIR /aithena_agent_chat

EXPOSE $PORT

ENV PORT=$PORT

CMD ["solara", "run", "src/polus/aithena/chat-app/dashboard.py", "--host=0.0.0.0", "--production"]