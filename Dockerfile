FROM python:3.12.4-slim@sha256:f11725aba18c19664a408902103365eaf8013823ffc56270f921d1dc78a198cb AS python

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
