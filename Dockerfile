FROM python:3.8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .

EXPOSE 5000
CMD ["python", "bot/main.py"]