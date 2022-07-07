FROM ubuntu:20.04
RUN apt-get update
RUN apt-get install -y openssh-client build-essential
RUN apt-get install -y python2 python-dev python-crypto pipenv
COPY Pipfile Pipfile.lock /briefkasten/
WORKDIR /briefkasten
ENV SHELL=/bin/bash
RUN pipenv sync
CMD pipenv shell --fancy
