#!/bin/bash
# Linux/Mac launcher — use run.bat on Windows
mkdir -p data
IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
echo "WAPP Market Simulator"
echo "URL: http://$IP:8501"
streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true --browser.gatherUsageStats false
