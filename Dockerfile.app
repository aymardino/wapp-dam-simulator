# API + compiled front end in a single image
FROM node:20-alpine AS web
WORKDIR /web
COPY web/package.json ./
RUN npm install
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY engine/ engine/
COPY api/ api/
COPY --from=web /web/dist web/dist
COPY deploy/healthcheck.py deploy/healthcheck.py
RUN mkdir -p data
# Port: 8000 by default (docker-compose), or the PORT variable provided by the platform (Render).
# The process runs as root inside the container: Render persistent disks are mounted for root.
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python deploy/healthcheck.py
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'"]
