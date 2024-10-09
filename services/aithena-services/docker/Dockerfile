FROM python:3.11-slim

RUN apt update && \
    apt upgrade -y

COPY . /aithena_services_src

RUN pip3 install -e /aithena_services_src --no-cache-dir
WORKDIR /aithena_services_src/api

EXPOSE 80

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "80", "main:app"]
