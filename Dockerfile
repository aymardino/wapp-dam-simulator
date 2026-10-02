# Simulateur Day-Ahead WAPP — image de déploiement
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data
EXPOSE 8501
# Mot de passe administrateur : à surcharger au lancement (docker run -e WAPP_ADMIN_PASSWORD=...)
ENV WAPP_ADMIN_PASSWORD=<mot-de-passe-retire>
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true", "--browser.gatherUsageStats", "false"]
