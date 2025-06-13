FROM python:3.13.5-slim@sha256:f2fdaec50160418e0c2867ba3e254755edd067171725886d5d303fd7057bbf81 AS python

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
