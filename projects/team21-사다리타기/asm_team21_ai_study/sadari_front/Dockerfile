FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./requirements.txt
COPY sadari_front/requirements.txt ./sadari_front/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r sadari_front/requirements.txt

COPY src ./src
COPY sadari_front/app ./sadari_front/app

EXPOSE 8000 8501
