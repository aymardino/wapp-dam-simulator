# Mettre en ligne wapp-dam-simulator.mastereose.fr

*Guide pratique, 2 octobre 2026 (version anglaise à jour : `docs/DEPLOYMENT.md` ; le nettoyage d'historique décrit en section 3 a été effectué le 3 octobre 2026). Quatre parties : ce qu'il faut acheter, publier le dépôt, installer le serveur, exploiter. Les sections sur l'exécution locale et en salle de formation sont à la fin.*

## 1. Architecture en production

```
Internet ──HTTPS 443──▶ Caddy (certificat Let's Encrypt automatique)
                           │
                           └──HTTP 8000──▶ api (uvicorn) : site vitrine + application + API REST
                                              └── volume wapp-data : data/rooms.db (salles, ordres, clearings)
```

Une seule image Docker (`Dockerfile.app`) compile le front React et emballe l'API ; `docker-compose.yml` l'assemble avec Caddy sur un serveur, `render.yaml` la déploie sur Render (section 4). Le site vitrine est servi à `/`, l'application (hall des salles) à `/app`, l'API à `/api/v1`, sa documentation à `/docs`.

## 2. Ce qu'il faut acheter

| Poste | Choix recommandé | Ordre de prix |
|---|---|---|
| Nom de domaine | `wapp-dam-simulator.mastereose.fr`, sous-domaine fourni par le Mastère OSE (enregistrement DNS géré par l'école) | gratuit |
| Serveur virtuel | Hetzner CX22, OVH VPS, Scaleway DEV1-S : 2 vCPU, 4 Go, Ubuntu 24.04 | 4 à 8 € par mois |

Dimensionnement : un clearing de référence prend 0,5 s, un cas de formation avec blocs quelques secondes ; une salle de 20 participants tient sans difficulté sur 2 vCPU. Le disque nécessaire est de quelques dizaines de Mo.

Le sous-domaine est servi par un enregistrement DNS (CNAME ou A) vers le serveur, ou par un relais de la DSI vers le port 443. Un nom de domaine propre (chez un registrar : Gandi, OVH, Infomaniak, Namecheap ; 12 à 20 € par an) reste possible : la variable `DOMAIN` du fichier `.env` prend alors ce nom et, pour un domaine apex, on ajoute au `Caddyfile` un bloc `www.` qui redirige vers l'apex.

## 3. Publier le dépôt sur GitHub

Le serveur se déploie depuis le dépôt git ; la publication est aussi la condition de l'accès ouvert (licence Apache 2.0).

1. Créer sur github.com un dépôt public vide nommé `wapp-dam-simulator` (sans README ni licence : ils existent déjà).
2. Depuis le dossier du projet :

```bash
git remote add origin https://github.com/<compte>/wapp-dam-simulator.git
git push -u origin main
```

3. Mettre l'adresse réelle du dépôt dans `web/src/links.ts` (site vitrine) et dans `README.md`, puis recompiler et pousser.
4. Vérifier que l'action « tests » passe sur GitHub (moteur, API et compilation du front).

Avant le premier push, vérifications faites le 2 octobre 2026 et à refaire après toute modification :

- `data/`, `*.db`, `.env`, `.venv/`, `web/node_modules`, `web/dist` sont ignorés (`.gitignore`) ;
- aucun mot de passe dans le code ni dans l'historique : l'ancien mot de passe administrateur du Livrable 3
  (valeur par défaut de la page Administration de l'application Streamlit livrée) figure dans tous les commits
  antérieurs au 2 octobre 2026 au soir (`pages/3_Admin.py`, `README.md`, `Dockerfile`), et les anciens commits
  contiennent aussi le logo du WAPP et la carte Tractebel/CEDEAO. Les retirer de
  l'historique **avant** le premier push, depuis le dossier du projet (le dépôt n'a pas encore de remote, rien
  n'est perdu : une branche de sauvegarde est créée d'abord) :

```bash
export ANCIEN_MDP='<ancien mot de passe administrateur>'   # à saisir, sans le laisser dans l'historique du shell
git branch backup/avant-reecriture && FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f --tree-filter 'for f in README.md pages/3_Admin.py Dockerfile; do if [ -f "$f" ] && grep -q "$ANCIEN_MDP" "$f"; then LC_ALL=C sed -i "" "s/$ANCIEN_MDP/<mot-de-passe-retire>/g" "$f"; fi; done; rm -f assets/wapp_logo.png assets/wapp_map.png web/public/wapp_logo.png; true' -- main
```

  Vérifier ensuite que `git log main -p -S"$ANCIEN_MDP" | grep -c "$ANCIEN_MDP"` affiche `0`, puis supprimer la
  sauvegarde pour qu'elle ne parte jamais sur GitHub : `git branch -D backup/avant-reecriture && rm -rf .git/refs/original && git reflog expire --expire=now --all && git gc --prune=now` ;
- le logo du WAPP et la carte Tractebel/CEDEAO ne sont plus dans le dépôt courant (marque neutre `mark.svg`, carte Natural Earth générée) ;
- `LICENSE`, `NOTICE` et la mention de non-affiliation sont présents.

## 4. Option A : Render (plateforme gérée, recommandé si vous y avez déjà un compte)

Render construit l'image `Dockerfile.app` depuis GitHub et la met en ligne avec HTTPS ; aucune machine à administrer. Le fichier `render.yaml` à la racine décrit tout (service web Docker, disque persistant pour les salles, contrôle de santé, variables).

1. Pousser le dépôt sur GitHub (section 3).
2. Dans le tableau de bord Render : **New → Blueprint**, choisir le dépôt, valider. Render crée le service `wapp-dam-simulator` avec le plan Starter et un disque de 1 Go monté sur `/app/data`. La première construction prend 3 à 5 minutes (compilation du front puis installation de Python).
   Sans Blueprint : **New → Web Service → le dépôt → Runtime Docker**, *Dockerfile path* `Dockerfile.app`, *Health check path* `/api/v1/health`, puis onglet *Disks* : ajouter un disque monté sur `/app/data`, et onglet *Environment* : les variables de `.env.example`.
3. Vérifier `https://wapp-dam-simulator.onrender.com/api/v1/health`, puis créer une salle et lancer un clearing.
4. Nom de domaine : *Settings → Custom Domains → Add* `wapp-dam-simulator.mastereose.fr`. Render affiche l'enregistrement CNAME à faire créer par l'administrateur DNS du Mastère OSE et obtient le certificat tout seul. Mettre ensuite le domaine dans `WAPP_CORS_ORIGINS` (déjà le cas dans `render.yaml`).
5. Mises à jour : chaque `git push` sur `main` redéploie (*autoDeploy*). Sauvegardes : *Disks → Snapshots* (quotidiens, conservés 7 jours) ; pour une copie locale, `render ssh` puis `sqlite3 /app/data/rooms.db .dump`.

Points d'attention : le plan Free n'accepte pas de disque (les salles seraient perdues à chaque redémarrage) et endort le service après quinze minutes d'inactivité ; prendre le plan Starter (7 $/mois, plus 0,25 $/mois le disque). Avec un disque attaché, un déploiement coupe le service quelques secondes. Le conteneur écoute sur le port fourni par Render (`PORT`), l'image gère les deux cas.

## 4 bis. Option B : serveur virtuel (une fois)

1. Faire créer par l'administrateur DNS du Mastère OSE un enregistrement `A` `wapp-dam-simulator.mastereose.fr` vers l'adresse IPv4 du serveur (ou un `CNAME` vers son nom). Compter jusqu'à une heure de propagation.
2. Se connecter au serveur et lancer le script d'installation (il installe Docker et le pare-feu, clone le dépôt, crée `.env`, démarre les services) :

```bash
ssh root@<adresse-du-serveur>
curl -fsSL https://raw.githubusercontent.com/<compte>/wapp-dam-simulator/main/deploy/setup_server.sh -o setup_server.sh
bash setup_server.sh https://github.com/<compte>/wapp-dam-simulator.git wapp-dam-simulator.mastereose.fr
```

3. Vérifier : `https://wapp-dam-simulator.mastereose.fr` affiche le site, `https://wapp-dam-simulator.mastereose.fr/api/v1/health` répond `{"status":"ok", …}`. Le certificat est obtenu au premier accès (quelques secondes).
4. Créer une salle, la rejoindre depuis un téléphone, lancer un clearing.

Le fichier `/opt/wapp/app/.env` contient les réglages (modèle dans `.env.example`) :

| Variable | Rôle | Défaut |
|---|---|---|
| `DOMAIN` | nom servi par Caddy | wapp-dam-simulator.mastereose.fr |
| `WAPP_CORS_ORIGINS` | origines autorisées pour l'API | https://wapp-dam-simulator.mastereose.fr |
| `WAPP_ROOM_TTL_DAYS` | purge des salles inactives | 30 |
| `WAPP_MAX_ROOMS_PER_IP_PER_DAY` | quota de création de salles | 20 |

## 5. Exploiter

| Besoin | Commande (sur le serveur, dans `/opt/wapp/app`) |
|---|---|
| Mettre à jour après un `git push` | `deploy/update.sh` |
| Sauvegarder les salles | `deploy/backup.sh` (archives dans `/opt/wapp/backups`, 14 jours) |
| Sauvegarde automatique chaque nuit | `echo '0 3 * * * /opt/wapp/app/deploy/backup.sh' \| crontab -` |
| Journaux | `docker compose logs -f api` |
| État des services | `docker compose ps` |
| Redémarrer | `docker compose restart` |
| Repartir de zéro (efface les salles) | `docker compose down -v && docker compose up -d` |

Le serveur ne demande aucune maintenance quotidienne : Caddy renouvelle le certificat, l'API purge les salles inactives, Docker redémarre les services après un redémarrage de la machine. Prévoir `apt upgrade` de temps en temps.

### Autres plateformes gérées

Fly.io ou Railway fonctionnent comme Render avec `Dockerfile.app` : prévoir un disque persistant monté sur `/app/data` (ou `WAPP_API_DATABASE_URL` vers un Postgres géré, avec `psycopg[binary]` dans l'image) et définir `WAPP_CORS_ORIGINS`. Streamlit Community Cloud ne convient pas (il n'héberge que des applications Streamlit).

## 6. Avant d'annoncer le site

- `web/src/links.ts` : adresse du dépôt, de la note technique quand elle paraît.
- Tester depuis un téléphone : page d'accueil, création d'une salle, dépôt d'ordres, clearing.
- Les textes d'avertissement (simulateur indépendant, NTC estimées) sont sur la page d'accueil et dans `NOTICE`.
- Une sauvegarde a été faite et restaurée au moins une fois.

## 7. Sur votre poste (développement et démonstration)

Prérequis : Python 3.10 ou plus récent, Node 20 ou plus récent (pour le front).

```bash
python -m venv .venv && source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cd web && npm install && npm run build && cd ..          # compile le front dans web/dist
uvicorn api.main:app --reload --port 8000
```

Ouvrez `http://localhost:8000` (site vitrine), `http://localhost:8000/app` (salles) et `http://localhost:8000/docs` (API). Pour développer le front avec rechargement à chaud : `cd web && npm run dev`, puis `http://localhost:5173` (les appels `/api` sont relayés vers le port 8000). L'application Streamlit historique reste disponible : `streamlit run app.py`.

Données : l'API écrit `data/rooms.db` (SQLite). Pour repartir de zéro, supprimez ce fichier. Base Postgres : `export WAPP_API_DATABASE_URL=postgresql+psycopg://user:mdp@hote/base`.

Image Docker locale, identique à la production :

```bash
docker build -f Dockerfile.app -t wapp-simulator .
docker run -d --name wapp -p 8000:8000 -v wapp-data:/app/data wapp-simulator
```

## 8. Sur un réseau de formation (salle, hotspot)

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Les participants ouvrent `http://<adresse-IP-du-formateur>:8000/app` et saisissent le code de la salle. Si le pare-feu de l'établissement bloque le port, un point d'accès Wi-Fi depuis un téléphone ou un tunnel (`ssh -R 80:localhost:8000 nokey@localhost.run`) contourne la difficulté. Avec le site en ligne, le plus simple reste d'utiliser `https://wapp-dam-simulator.mastereose.fr/app`.

## 9. Vérifier que tout fonctionne

```bash
pytest -q                                   # moteur, base, API, ligne de commande, cas aléatoires
curl http://localhost:8000/api/v1/health    # {"status":"ok", ...}
curl http://localhost:8000/api/v1/demo      # clearing de démonstration du site vitrine (mis en cache)
```
