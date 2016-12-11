FROM python:3
MAINTAINER david@tucker.name

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /src
COPY . .
RUN rm -rf dist
RUN ./setup.py sdist
RUN pip install dist/*
