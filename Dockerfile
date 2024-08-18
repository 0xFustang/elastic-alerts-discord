FROM python:3.12.4-slim-bookworm

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get clean

COPY elastic-alerts-discord.py requirements.txt /app/

WORKDIR /app

RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt

ENV TZ="Europe/Paris"

ENTRYPOINT ["python3", "./elastic-alerts-discord.py"]