FROM python:3.14.6-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS python

FROM python AS app
RUN apt update
RUN apt install --yes gnupg
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1 /uv /uvx /bin/
WORKDIR /application
COPY /application .
RUN uv sync --frozen

FROM app AS backend-testing
RUN pip install tox
ENTRYPOINT  ["tox"]
