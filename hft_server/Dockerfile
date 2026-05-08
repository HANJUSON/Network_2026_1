FROM python:3.11-slim

# tc netem 사용을 위한 iproute2 설치
RUN apt-get update && apt-get install -y iproute2 && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . .

EXPOSE 8888/tcp
EXPOSE 8888/udp

CMD ["python", "main_server.py"]
