"""Health check of the Docker image: exits 0 when the API answers on the listening port (PORT or 8000)."""
import os, sys, urllib.request
try:
    r = urllib.request.urlopen(f"http://127.0.0.1:{os.environ.get('PORT', '8000')}/api/v1/health", timeout=4)
    sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
