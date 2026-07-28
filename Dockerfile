FROM python:3.14.6-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS python

FROM python AS app
RUN apt update
RUN apt install --yes gnupg
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:ecd4de2f060c64bea0ff8ecb182ddf46ba3fcccdc8a60cfdbaf20d1a047d7437 /uv /uvx /bin/
WORKDIR /application
COPY /application .
RUN uv sync --frozen

FROM app AS backend-testing
RUN pip install tox
ENTRYPOINT  ["tox"]
