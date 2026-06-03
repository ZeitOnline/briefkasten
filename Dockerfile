FROM python:3.14.5-slim@sha256:c845af9399020c7e562969a13689e929074a10fd057acd1b1fad06a2fb068e97 AS python

FROM python AS app
RUN apt update
RUN apt install --yes gnupg
WORKDIR /application
COPY /application/requirements.txt .
RUN pip install --upgrade setuptools pip wheel
RUN pip install --requirement requirements.txt
COPY /application .

FROM app AS backend-testing
RUN pip install tox
ENTRYPOINT tox
