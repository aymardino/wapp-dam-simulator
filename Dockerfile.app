# API + front compilé dans une seule image
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
# Port : 8000 par défaut (docker-compose), ou la variable PORT fournie par la plateforme (Render).
# Le processus tourne en root dans le conteneur : les disques persistants de Render sont montés pour root.
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python deploy/healthcheck.py
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'"]
