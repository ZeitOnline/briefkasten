FROM python:3.14.7-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4 AS python

FROM ghcr.io/astral-sh/uv:0.12.5@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1 AS uv

FROM python AS app
RUN apt update
RUN apt install --yes gnupg
COPY --from=uv /uv /uvx /bin/
WORKDIR /application
COPY /application .
RUN uv sync --frozen

FROM app AS backend-testing
RUN pip install tox
ENTRYPOINT  ["tox"]
