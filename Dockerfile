FROM python:3.11.3-slim AS python

FROM python AS app
RUN apt update
RUN apt install --yes gnupg git
WORKDIR /application
COPY /application/requirements.txt .
RUN pip install --upgrade setuptools pip wheel
RUN pip install --requirement requirements.txt
COPY /application .

FROM app AS backend-testing
RUN pip install tox
ENTRYPOINT tox
