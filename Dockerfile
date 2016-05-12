FROM python:3
MAINTAINER david.michael.tucker@gmail.com

RUN pip install --upgrade pip
RUN pip install pep8 pylint

WORKDIR /src
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN pep8 setup.py
RUN pylint setup.py
RUN pep8 searents
RUN pylint searents
RUN rm -rf dist
RUN python setup.py sdist
RUN pip install dist/*
WORKDIR /

ENTRYPOINT ["searents"]
