FROM python:3.10.4-slim

ENV API_KEY=???
ENV SECRET_KEY=???

WORKDIR /app

COPY requirements.txt ./

RUN apt-get update -y
RUN apt-get install nano -y
RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .