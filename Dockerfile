FROM python:3.13.7-slim@sha256:f247c2a5079b2a6704a8deaee6c5117f627fe538718bda0924837a398d951570 AS python

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
