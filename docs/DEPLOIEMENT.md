# Exécuter et héberger le simulateur

*Guide pratique, 2 octobre 2026. Trois niveaux : sur votre poste, sur un réseau de formation, sur Internet.*

## 1. Sur votre poste (développement et démonstration)

Prérequis : Python 3.10 ou plus récent, Node 20 ou plus récent (pour le nouveau front seulement).

```bash
# une seule fois
python -m venv .venv && source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cd web && npm install && npm run build && cd ..          # compile le front dans web/dist

# à chaque session
uvicorn api.main:app --port 8000
```

Ouvrez `http://localhost:8000` : le hall permet de créer une salle (formateur) ou d'en rejoindre une (trader). La documentation de l'API est sur `http://localhost:8000/docs`.

Pour développer le front avec rechargement à chaud, lancez en plus `cd web && npm run dev` et ouvrez `http://localhost:5173` (les appels `/api` sont relayés vers le port 8000).

L'application Streamlit historique reste disponible : `streamlit run app.py`.

Données : l'API écrit `data/rooms.db` (SQLite). Pour repartir de zéro, supprimez ce fichier. Pour une base Postgres : `export WAPP_API_DATABASE_URL=postgresql+psycopg://user:mdp@hote/base` (installer `psycopg[binary]`).

## 2. Sur un réseau de formation (salle, hotspot)

Même commande, en écoutant sur toutes les interfaces :

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Les participants ouvrent `http://<adresse-IP-du-formateur>:8000` et saisissent le code de la salle. Si le pare-feu de l'établissement bloque le port, un point d'accès Wi-Fi depuis un téléphone ou un tunnel (`ssh -R 80:localhost:8000 nokey@localhost.run`) contourne la difficulté, comme avec Streamlit.

## 3. Sur Internet (démo publique, formations à distance)

### Image Docker (recommandé, identique partout)

`Dockerfile.app` compile le front et emballe l'API dans une seule image :

```bash
docker build -f Dockerfile.app -t wapp-simulator .
docker run -d --name wapp -p 8000:8000 -v wapp-data:/app/data wapp-simulator
```

Le volume `wapp-data` conserve les salles entre deux redémarrages.

### Serveur virtuel avec HTTPS et nom de domaine (recommandé pour le site public)

1. Louer un petit serveur (OVH, Hetzner, Scaleway : 1 vCPU et 2 Go suffisent, 5 à 10 € par mois) sous Ubuntu, et y installer Docker.
2. Acheter le nom de domaine choisi et faire pointer un enregistrement A vers l'adresse du serveur.
3. Copier le dépôt sur le serveur et lancer `docker compose up -d` avec le fichier `docker-compose.yml` fourni : il démarre l'API et un serveur Caddy qui obtient et renouvelle le certificat HTTPS automatiquement. Remplacer `wapp-dam-simulator.org` dans `Caddyfile` par votre domaine.
4. Mises à jour : `git pull && docker compose up -d --build`.
5. Sauvegardes : copier régulièrement le volume `wapp-data` (une commande `docker run --rm -v wapp-data:/data -v $PWD:/backup alpine tar czf /backup/wapp-data.tgz /data`).

### Plateformes gérées (plus simple, moins de contrôle)

Render, Railway ou Fly.io déploient directement depuis GitHub avec `Dockerfile.app` ; prévoir un disque persistant pour `/app/data` ou une base Postgres gérée. Streamlit Community Cloud ne convient pas à l'API (il n'héberge que des applications Streamlit).

## 4. Avant une mise en ligne publique

- Définir `WAPP_CORS_ORIGINS` sur le domaine du site (par défaut toutes les origines sont acceptées, pratique en développement).
- Ajouter une expiration des salles inactives et une limite de création par adresse (prévu, pas encore fait).
- Afficher l'avertissement sur les données de référence (NTC estimées) sur la page d'accueil du site vitrine.
- Choisir la licence du code et le nom public, et vérifier l'usage du logo WAPP.
- Surveiller les journaux : `docker compose logs -f api`.

## 5. Vérifier que tout fonctionne

```bash
pytest -q                                   # 27 tests : moteur, base, API, ligne de commande
curl http://localhost:8000/api/v1/health    # {"status":"ok", ...}
```
