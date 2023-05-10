FROM python:3.11-slim

WORKDIR /home/flask-app

COPY ./requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update && \
    apt-get install -y curl
COPY . .

EXPOSE 5000