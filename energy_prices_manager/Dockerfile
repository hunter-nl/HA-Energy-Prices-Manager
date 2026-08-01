ARG BUILD_FROM=python:3.14-slim
FROM ${BUILD_FROM}

ARG BUILD_ARCH
ARG BUILD_VERSION

LABEL \
  io.hass.type="app" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.arch="${BUILD_ARCH}" \
  org.opencontainers.image.source="https://github.com/hunter-nl/HA-Energy-Prices-Manager"

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi==0.128.0 \
    "uvicorn[standard]==0.40.0" \
    websockets==16.0

COPY app /app/app
COPY web /app/web
COPY run.sh /run.sh

RUN chmod a+x /run.sh

CMD ["/run.sh"]
