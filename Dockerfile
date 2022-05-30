FROM python:3.10.4-slim

ENV API_KEY=xxx
ENV SECRET_KEY=xxx

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]
