FROM ubuntu:18.04

RUN apt-get update -y && \
    apt-get install -y python3-pip python3.7

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

RUN pip3 install -r /app/requirements.txt