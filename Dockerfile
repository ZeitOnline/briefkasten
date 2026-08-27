FROM python:3.14.7-slim@sha256:cae66f2ef0ec51a9891263eeee7f987dacf0a9879e8aa9353d5606e0530619a5 AS python

FROM ghcr.io/astral-sh/uv:0.12.6@sha256:88bc6eb1ccd4b82efd0e1b530caffabddf50dc2bf612e66c14ea25b8ee8a4d3d AS uv

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
