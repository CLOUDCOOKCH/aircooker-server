# syntax=docker/dockerfile:1
FROM node:24-alpine@sha256:44fce696f38ba8c987c4db89954051000bbd05ffd8d8659ba15ed4a8602e937f AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; \
    npm ci --ignore-scripts --no-fund
COPY frontend ./
RUN npm run build
FROM python:3.12.14-alpine3.24@sha256:4c47124a8391cb7a9f571164147d154777cf012a4ece5f86097130d7a4478111 AS base
FROM base AS builder
WORKDIR /build
COPY pyproject.toml requirements.lock ./
COPY src ./src
COPY --from=frontend /build/frontend/dist ./src/aircooker/web/pwa
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    python -m pip wheel --require-hashes --wheel-dir /wheels -r requirements.lock && \
    python -m pip wheel --no-deps --wheel-dir /wheels .
FROM base AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data LOG_LEVEL=info TRUSTED_PROXY_CIDRS=""
RUN --mount=type=secret,id=proxy_ca,target=/etc/ssl/cert.pem \
    apk add --no-cache bash=5.3.9-r1 tesseract-ocr=5.5.2-r0 tesseract-ocr-data-eng=5.5.2-r0 tesseract-ocr-data-deu=5.5.2-r0
RUN addgroup -g 10001 aircooker && adduser -u 10001 -G aircooker -D -H aircooker && mkdir /data && chown 10001:10001 /data
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels aircooker-server && rm -rf /wheels
WORKDIR /app
USER 10001:10001
VOLUME ["/data"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/v1/system/health', timeout=3)"]
CMD ["python", "-m", "aircooker"]
