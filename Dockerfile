FROM debian:latest
MAINTAINER david.michael.tucker@gmail.com
RUN apt-get update && apt-get install -y \
    python-matplotlib \
    python-numpy \
    python-pip
RUN pip install \
    fake-useragent \
    requests
COPY . /
ENTRYPOINT ["python"]
