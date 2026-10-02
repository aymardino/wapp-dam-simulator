# Architecture v2 : moteur, API, salle de marché

*2 octobre 2026. Complète `docs/REGLES_DE_MARCHE.md` (règles) et `CHANGELOG.md` (historique).*

## Vue d'ensemble

```
engine/            moteur de clearing (Pyomo + HiGHS), règles explicites, tests      → inchangé par l'API
   clearing.py     run_clearing(...)  →  prices, flows, dispatch, summary
   cli.py          python -m engine.cli : CSV en entrée, JSON en sortie
api/               FastAPI : salles de marché multi-participants, ordres, clearings    → uvicorn api.main:app
   storage.py      SQLAlchemy (SQLite par défaut, Postgres via WAPP_API_DATABASE_URL)
   schemas.py      contrats d'entrée/sortie (pydantic), validation des ordres
   service.py      adaptateur salle → lignes du moteur, exécution, résultat du trader
   auth.py         jeton de participant (Authorization: Bearer)
   main.py         routes /api/v1, sert web/dist si présent
web/               front React (Vite, Tailwind) : hall, salle de marché, poste du formateur
app.py, pages/     application Streamlit historique (formation locale), toujours fonctionnelle
```

Le moteur ne connaît ni les salles ni les participants : l'API lui passe des lignes (zone, trader, acteur, …) exactement comme l'application Streamlit. Les deux interfaces partagent donc les mêmes règles et les mêmes tests.

## Modèle de données de l'API

| Objet | Champs | Rôle |
|-------|--------|------|
| Salle (`rooms`) | code à 6 caractères, nom, phase (`submission` / `cleared`), paramètres (heures, règles, monnaie, langue, date), NTC surchargées | une formation ou une démonstration |
| Participant (`participants`) | nom (organisation), zone, rôle (`trainer` / `trader` / `observer`), jeton | une personne connectée ; plusieurs traders par zone possibles |
| Ordre (`orders`) | participant, type (`supply` / `demand` / `block` / `mic`), contenu JSON | le carnet d'ordres d'un trader, remplacé en bloc à chaque dépôt |
| Clearing (`clearing_runs`) | date, paramètres figés, welfare, volume, résultat complet JSON | historique des exécutions d'une salle |

Le formateur reçoit son jeton à la création de la salle ; les traders le reçoivent en rejoignant. Le jeton est porté dans l'en-tête `Authorization: Bearer …`. Il n'y a pas de comptes ni de mots de passe : une salle est une pièce fermée dont le code est la clé, ce qui correspond à l'usage en formation. Pour une exposition publique durable, ajouter une expiration des salles et un quota par adresse.

## Routes

| Méthode et route | Qui | Effet |
|------------------|-----|-------|
| `GET /api/v1/reference` | tous | zones, lignes et NTC par défaut, profils, bornes de prix, règles disponibles, données de référence |
| `POST /api/v1/rooms` | formateur | crée une salle, renvoie le code et le jeton du formateur |
| `GET /api/v1/rooms/{code}` | tous | état complet (paramètres, NTC effectives, participants, compteurs, dernier clearing) |
| `GET /api/v1/rooms/{code}/state` | tous | état léger pour le rafraîchissement périodique |
| `POST /api/v1/rooms/{code}/join` | trader, observateur | rejoint la salle, renvoie un jeton |
| `GET /api/v1/rooms/{code}/me` | participant | identité liée au jeton |
| `PUT /api/v1/rooms/{code}/settings` | formateur | heures simulées, règles de prix, de blocs paradoxaux et de partage, complétion, monnaie, langue, date |
| `PUT /api/v1/rooms/{code}/phase` | formateur | ouvre ou clôture la soumission |
| `PUT` / `DELETE /api/v1/rooms/{code}/ntc` | formateur | surcharge ou restaure les NTC |
| `GET` / `PUT /api/v1/rooms/{code}/orders/me` | trader | lit ou remplace son carnet d'ordres (refusé si la soumission est clôturée) |
| `GET` / `DELETE /api/v1/rooms/{code}/orders` | formateur | tous les carnets ; suppression générale |
| `POST /api/v1/rooms/{code}/clearing` | formateur | exécute le moteur avec les ordres de la salle, enregistre, clôture |
| `GET /api/v1/rooms/{code}/results` | tous | historique des clearings |
| `GET /api/v1/rooms/{code}/results/{id|latest}` | tous | résultat complet (prix, flux, dispatch, résumé, diagnostics) |
| `GET /api/v1/rooms/{code}/results/{id|latest}/me` | participant | résultat du trader : ses acteurs, ses blocs, ses MIC, les prix de sa zone |

Les erreurs du moteur (`ClearingError`) reviennent en 422 avec le message en clair. La documentation interactive est servie sur `/docs`.

## Front

Trois écrans, un seul système de design :

- **Hall** (`/`) : créer une salle ou en rejoindre une.
- **Salle de marché** (`/room/:code`) : à gauche le carnet d'ordres du trader (segments, blocs, MIC), au centre le marché (prix par zone et par heure, positions nettes, dernier clearing), à droite son résultat (volumes, surplus, ordres rejetés, prix de sa zone).
- **Poste du formateur** (`/desk/:code`) : indicateurs, lancement du clearing, phase, paramètres et règles, NTC, participants et ordres, vérifications de cohérence, synthèse par zone.

Système de design : palette neutre (`page`, `surface`, `panel`, `ink`, `line`) et un seul accent (vert profond), deux poids de police (400, 500), chiffres en police à chasse fixe, filets fins plutôt que cartes bordées, couleur réservée au sens (position nette, statut d'un bloc). L'ensemble est défini dans `web/tailwind.config.js` et `web/src/styles.css`.

Le front interroge l'API toutes les dix secondes (`/state`, puis `/results/latest` quand un nouveau clearing apparaît). Un canal temps réel (SSE ou WebSocket) remplacera ce sondage dans une version ultérieure.

## Lancer l'ensemble en développement

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000        # API + documentation sur /docs
cd web && npm install && npm run dev             # front sur http://localhost:5173 (proxy /api → 8000)
```

En production : `npm run build` produit `web/dist`, que l'API sert à la racine ; une seule image Docker suffit (`Dockerfile.app`).

## Ce qui reste

Carte des zones avec prix et flux, graphiques (ECharts), temps réel, expiration des salles, export Excel, scénarios préenregistrés, tests de bout en bout du front.
