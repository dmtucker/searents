FROM python:3
MAINTAINER david.michael.tucker@gmail.com

RUN pip install --upgrade pip

# Build and install the project.
WORKDIR /src
COPY . .
RUN rm -rf dist
RUN python setup.py sdist
RUN pip install dist/*
WORKDIR /

ENTRYPOINT ["searents"]
