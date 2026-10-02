# WAPP Day-Ahead simulator (Streamlit application) — deployment image
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data
EXPOSE 8501
# Administrator password: required at launch (docker run -e WAPP_ADMIN_PASSWORD=...), no default.
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true", "--browser.gatherUsageStats", "false"]
