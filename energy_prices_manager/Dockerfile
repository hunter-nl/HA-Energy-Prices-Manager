FROM python:3.14-slim

ARG BUILD_ARCH=amd64
ARG BUILD_VERSION=dev

LABEL \
  io.hass.type="app" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.arch="${BUILD_ARCH}" \
  io.hass.name="Energy Prices Manager" \
  io.hass.description="Manage energy tariff periods and Home Assistant price helpers" \
  io.hass.url="https://github.com/hunter-nl/HA-Energy-Prices-Manager" \
  org.opencontainers.image.title="Energy Prices Manager" \
  org.opencontainers.image.description="Manage energy tariff periods and Home Assistant price helpers" \
  org.opencontainers.image.source="https://github.com/hunter-nl/HA-Energy-Prices-Manager" \
  org.opencontainers.image.licenses="AGPL-3.0-only"

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
