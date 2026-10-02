"""Contrôle de santé de l'image Docker : répond 0 si l'API répond sur le port d'écoute (PORT ou 8000)."""
import os, sys, urllib.request
try:
    r = urllib.request.urlopen(f"http://127.0.0.1:{os.environ.get('PORT', '8000')}/api/v1/health", timeout=4)
    sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
