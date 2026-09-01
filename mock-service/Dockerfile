FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NSC_DATA_FILE=/app/data/records.json

RUN apt-get update \
    && apt-get install --no-install-recommends -y nginx supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/mock-service

COPY api /opt/mock-service/api
COPY auth /opt/mock-service/auth
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY json /opt/mock-service/json
COPY data/records.json /app/data/records.json
COPY supervisord.conf /etc/supervisor/conf.d/mock-service.conf

RUN python -m pip install --no-cache-dir \
    "fastapi>=0.115" \
    "PyJWT>=2.9" \
    "python-multipart>=0.0.9" \
    "pydantic-settings>=2.5" \
    "uvicorn[standard]>=0.30" \
    && mkdir -p /etc/nginx/certs /var/log/supervisor

EXPOSE 8443 9000

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
