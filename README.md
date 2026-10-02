# WAPP Day-Ahead Market Simulator

**Outil de formation et implémentation ouverte de référence du couplage de marché day-ahead zonal appliqué au West African Power Pool**
Projet MS OSE 2025 — Mines Paris-PSL × SENELEC × EPEX SPOT · version 2 (octobre 2026)

*English summary at the end of this file.*

---

## Ce que fait l'outil

Chaque participant se connecte comme trader d'un pays, dépose ses offres de vente et d'achat pour chaque heure du lendemain, et l'administrateur lance le clearing. Le moteur répond à trois questions, dans l'ordre : **qui échange** (la combinaison d'échanges qui crée le plus de valeur sans dépasser la capacité des lignes), **comment départager** les ex æquo (le plus d'énergie échangée), **à quel prix** (un prix par pays et par heure, choisi dans l'ensemble des prix compatibles avec les quantités). Les règles sont écrites noir sur blanc dans [docs/REGLES_DE_MARCHE.md](docs/REGLES_DE_MARCHE.md) et vérifiées par des tests.

Nouveautés de la version 2 (détail dans [CHANGELOG.md](CHANGELOG.md)) :
- ordres bloc, liés et exclusifs réellement modélisés (MILP), blocs paradoxaux traités selon la règle EUPHEMIA ;
- condition de revenu minimum (MIC) avec retrait itératif, règle explicite de partage des offres au même prix ;
- prix zonaux choisis dans l'ensemble admissible complet (plus d'ordre paradoxalement rejeté, plus d'écart de prix sans congestion) ;
- NTC modifiables, heure simulée au choix, zones manquantes complétées, messages d'erreur lisibles ;
- vue « Mon résultat » pour chaque trader, décomposition du welfare, diagnostics de cohérence ;
- interface bilingue français / anglais, monnaie paramétrable ;
- suite de tests calée sur les valeurs du Livrable 2, Dockerfile.

---

## Installation

Prérequis : Python 3.10 ou plus récent.

```bash
pip install -r requirements.txt
```

Le solveur HiGHS (paquet `highspy`) est installé avec les dépendances et suffit pour tous les cas, blocs compris, en moins d'une seconde. Gurobi est utilisé automatiquement s'il est présent.

## Lancement

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

ou `run.sh` (Linux, macOS) / `run.bat` (Windows). L'application s'ouvre sur `http://localhost:8501`.

Avec Docker :

```bash
docker build -t wapp-simulator .
docker run -p 8501:8501 -e WAPP_ADMIN_PASSWORD=motdepasse wapp-simulator
```

### Mot de passe administrateur

Défini par la variable d'environnement `WAPP_ADMIN_PASSWORD` ou par la clé `admin_password` dans `.streamlit/secrets.toml`. À défaut : `<mot-de-passe-retire>` (à changer avant toute mise en ligne).

### Accès multi-utilisateurs en formation

Les participants ouvrent `http://[adresse-du-formateur]:8501` sur le même réseau. Si le pare-feu bloque le port, deux solutions sans droits administrateur : un point d'accès Wi-Fi depuis un téléphone, ou un tunnel :

```bash
ssh -R 80:localhost:8501 nokey@localhost.run
```

L'URL `https://xxxx.lhr.life` affichée est à partager. Les données transitent alors par les serveurs du service de tunnel : à réserver aux données de formation.

Limite connue de Streamlit : rafraîchir la page du navigateur déconnecte le trader ; il suffit de se reconnecter depuis la barre latérale.

---

## Déroulé d'une session

1. **Connexion** : chaque trader choisit son pays et son organisation (plusieurs organisations par pays possibles).
2. **Soumission** : offres par segments (prix croissants, profil horaire) et ordres bloc (simples, liés à un parent, ou en groupe exclusif).
3. **Clearing** : l'administrateur choisit l'horizon (24 h ou une heure précise), la règle de prix, la règle de traitement des blocs paradoxaux, le sort des zones sans soumission, puis lance le calcul.
4. **Résultats** : prix, flux, dispatch, ordres bloc, résultat individuel de chaque trader, analyse (surplus, rente de congestion, vérifications), tableaux et export.

---

## Architecture

```
wapp_simulator/
├── app.py                    ← accueil, connexion des traders
├── ui_common.py              ← CSS, en-tête, bilinguisme FR/EN, monnaie
├── pages/
│   ├── 1_Submit_Offers.py    ← segments et ordres bloc
│   ├── 2_Results.py          ← résultats, vue trader, analyse
│   └── 3_Admin.py            ← phase, paramètres, règles, NTC, clearing
├── engine/
│   ├── clearing.py           ← moteur P1 / P1bis / P2, blocs, diagnostics
│   ├── db.py                 ← état partagé SQLite (offres, blocs, NTC, résultats)
│   └── actors.py             ← acteurs prédéfinis par zone
├── tests/test_engine.py      ← tests de non-régression (valeurs du Livrable 2)
├── docs/REGLES_DE_MARCHE.md  ← règles appliquées, en toutes lettres
├── assets/                   ← style, logo, carte
├── data/market.db            ← base SQLite locale (créée au premier lancement, jamais publiée)
├── CHANGELOG.md, AUDIT_V2.md, PLAN_VALORISATION.md
├── Dockerfile, requirements.txt, run.sh, run.bat
```

---

## Modèle

| Étape | Question | Problème | Type |
|-------|----------|----------|------|
| P1 | Qui échange ? | maximisation du welfare sous équilibre zonal, NTC, contrainte α, liaisons de blocs | LP, MILP avec blocs |
| P1bis | Comment départager ? | maximisation du volume à welfare optimal exact | LP |
| P2 | À quel prix ? | prix admissibles (conditions d'équilibre complètes) les plus proches du milieu de l'intervalle | LP |

Zones : NGA, BEN, TGO, GHA, CIV, BFA, MLI, SEN, GIN, SLE, LBR, GNB, GMB, NER. Interconnexions : 15 paires, flux signés. Contrainte d'interdépendance CIV/GHA/BFA avec α = 0,7.

| Type d'ordre | Modèle |
|--------------|--------|
| Segments prix / quantité (4 par acteur) | variables continues, acceptation partielle |
| Bloc simple | binaire, fill-or-kill sur sa plage horaire |
| Bloc lié | enfant ≤ parent |
| Groupe exclusif | au plus une option |
| Condition de revenu minimum (MIC) | recette ≥ terme fixe + terme variable × volume, sinon retrait et relance |

Blocs paradoxalement acceptés : rejetés itérativement (règle EUPHEMIA, par défaut). Blocs paradoxalement rejetés : tolérés et signalés. Offres au même prix : partage au prorata des quantités (ou par ordre de soumission).


## API et nouvelle application

Le moteur est aussi exposé par une API REST de salles de marché (plusieurs formations en parallèle, un code par salle, jetons de participants) et par une ligne de commande :

```bash
uvicorn api.main:app --reload --port 8000      # documentation interactive sur http://localhost:8000/docs
python -m engine.cli --reference --hours 19 --out resultat.json
```

Le nouveau front (React, dossier `web/`) se compile avec Node : `cd web && npm install && npm run build`, puis l'API le sert à la racine. Détails dans [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Tests

```bash
pip install pytest
pytest -q
```

Vingt et un tests reproduisent les valeurs du Livrable 2 (welfare 22 317 910 et volume 167 900 MWh sur le cas de référence, 23 082 419 avec blocs, 23 775 223 avec blocs liés et exclusifs) et vérifient les propriétés des prix. Les tests utilisent une base temporaire (`WAPP_DB_PATH`) et ne touchent jamais `data/market.db`.

## Données et confidentialité

- Les NTC et les profils horaires de référence sont des valeurs types estimées pour la formation, pas des données opérationnelles du WAPP. Ils se remplacent depuis la page Administration (NTC) et par les offres des participants.
- Tout fonctionne en local ; la base SQLite reste sur la machine hôte. Ne jamais publier le dossier `data/`.
- Monnaie : libellé paramétrable (USD par défaut), sans effet sur le calcul.

## Auteurs

Kodjovi Plakoo et Enrico Patanè (Mines Paris-PSL, MS OSE 2025), avec Lucien Kouakou, Mouhamadou Sow et Wissem Hmila (livrables 1 et 2). Encadrement : El Hadji Tamsir Diop (SENELEC) et Adrien Atayi (EPEX SPOT). Licence : à définir avant publication.

---

## English summary

An open, documented and tested implementation of day-ahead zonal market coupling for the West African Power Pool, built as a multi-user training tool. Traders log in as a country's organisation and submit stepwise orders (price/quantity segments shaped by hourly profiles) and block orders (simple, linked, exclusive). The administrator runs the clearing: P1 maximises welfare under zonal balance, NTC limits and a CIV/GHA/BFA interdependence constraint (LP, MILP with blocks); P1bis maximises traded volume among welfare-optimal solutions; P2 selects, within the complete set of admissible prices (full equilibrium conditions, network included), the price closest to the midpoint of the admissible interval. Paradoxically accepted blocks are iteratively rejected (EUPHEMIA rule); paradoxically rejected blocks are tolerated and reported. Equal-price orders are shared pro rata; minimum income conditions withdraw an actor's orders and re-run the clearing when its revenue falls short. Every rule is stated in `docs/REGLES_DE_MARCHE.md` and checked by `tests/test_engine.py`. Install with `pip install -r requirements.txt` (HiGHS solver included), run with `streamlit run app.py`, or use the Dockerfile. The interface is bilingual (French / English). Reference NTC values and profiles are illustrative estimates, not WAPP operational data.
