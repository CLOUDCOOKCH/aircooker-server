# syntax=docker/dockerfile:1
FROM python:3.12.14-slim-trixie@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f AS base
# Exact available security fixes identified by the container scan.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcre2-8-0=10.46-1~deb13u3 \
    libssl3t64=3.5.7-1~deb13u3 \
    openssl=3.5.7-1~deb13u3 \
    openssl-provider-legacy=3.5.7-1~deb13u3 \
    && rm -rf /var/lib/apt/lists/*
FROM base AS builder
WORKDIR /build
COPY pyproject.toml requirements.lock ./
COPY src ./src
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    python -m pip wheel --require-hashes --wheel-dir /wheels -r requirements.lock && \
    python -m pip wheel --no-deps --wheel-dir /wheels .
FROM base AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data LOG_LEVEL=info TRUSTED_PROXY_CIDRS=""
RUN groupadd --gid 10001 aircooker && useradd --uid 10001 --gid 10001 --no-create-home aircooker && mkdir /data && chown 10001:10001 /data
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels aircooker-server && rm -rf /wheels
WORKDIR /app
USER 10001:10001
VOLUME ["/data"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/v1/system/health', timeout=3)"]
CMD ["python", "-m", "aircooker"]
