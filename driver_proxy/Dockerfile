FROM python:3.9.15-slim-buster

COPY requirements.txt /app/

RUN python -m pip install -r /app/requirements.txt &&  \
    apt-get update &&  \
    apt-get install -y htop

COPY . ./app

WORKDIR /app

ENTRYPOINT ["python", "app.py"]
