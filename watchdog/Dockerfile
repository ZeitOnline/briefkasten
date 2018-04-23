FROM python:2 AS base
COPY requirements.txt .
RUN pip install --no-deps -r requirements.txt

# --- develop ---
FROM base AS develop
WORKDIR /build
RUN pip install pdbpp
COPY watchdog.ini .
# RUN pip install -e /src/watchdog/
ENTRYPOINT ["bash"]

# --- sdist ---
FROM base AS sdist
WORKDIR /build
COPY src/watchdog ./
RUN pip install -e .

# --- production ---
FROM sdist AS production
ENTRYPOINT ["watchdog"]
