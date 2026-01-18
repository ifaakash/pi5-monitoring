FROM python:3.10.19-slim

RUN apt-get update \
    && apt-get install -y iproute2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home

COPY ./monitoring.py ./

EXPOSE 8080

CMD ["python3", "monitoring.py"]
