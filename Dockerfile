FROM python:3.14-slim

LABEL \
  io.hass.version="3.0.0" \
  io.hass.type="app" \
  io.hass.arch="aarch64|amd64|armv7"

WORKDIR /app

RUN pip install --no-cache-dir fastapi==0.128.0 "uvicorn[standard]==0.40.0" websockets==16.0

COPY app /app/app
COPY custom_components/energy_prices_manager/www /app/web
COPY run.sh /run.sh

ENV ENERGY_PRICES_WEB_DIR=/app/web

RUN chmod a+x /run.sh

CMD ["/run.sh"]
