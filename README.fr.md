# WAPP Day-Ahead Market Simulator

**Outil de formation et implémentation ouverte de référence du couplage de marché day-ahead zonal appliqué au West African Power Pool**
Projet MS OSE 2025 — Mines Paris-PSL × SENELEC × EPEX SPOT · version 2 (octobre 2026)

*Version de référence en anglais : [README.md](README.md). Documentation française : [docs/fr/](docs/fr/).*

---

## Ce que fait l'outil

Chaque participant rejoint une salle au nom d'une organisation d'un pays, dépose ses offres de vente et d'achat pour chaque heure du lendemain, et le formateur lance le clearing. Le moteur répond à trois questions, dans l'ordre : **qui échange** (la combinaison d'échanges qui crée le plus de valeur sans dépasser la capacité des lignes), **comment départager** les ex æquo (le plus d'énergie échangée), **à quel prix** (un prix par pays et par heure, choisi dans l'ensemble des prix compatibles avec les quantités). Les règles sont écrites noir sur blanc dans [docs/fr/REGLES_DE_MARCHE.md](docs/fr/REGLES_DE_MARCHE.md) et vérifiées par des tests.

Nouveautés de la version 2 (détail dans [docs/fr/CHANGELOG.md](docs/fr/CHANGELOG.md)) :
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

Défini par la variable d'environnement `WAPP_ADMIN_PASSWORD` ou par la clé `admin_password` dans `.streamlit/secrets.toml`. Sans l'un des deux, la page Administration reste verrouillée (aucun mot de passe par défaut).

### Accès multi-utilisateurs en formation

Les participants ouvrent `http://[adresse-du-formateur]:8501` sur le même réseau. Si le pare-feu bloque le port, deux solutions sans droits administrateur : un point d'accès Wi-Fi depuis un téléphone, ou un tunnel :

```bash
ssh -R 80:localhost:8501 nokey@localhost.run
```

L'URL `https://xxxx.lhr.life` affichée est à partager. Les données transitent alors par les serveurs du service de tunnel : à réserver aux données de formation.

Limite connue de Streamlit : rafraîchir la page du navigateur déconnecte le trader ; il suffit de se reconnecter depuis la barre latérale.

---

## Guides

[Guide du formateur](docs/guides/formateur.fr.md) et [guide du trader](docs/guides/trader.fr.md), en français et en anglais, aussi accessibles depuis l'application (menu Guides).

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
├── docs/                     ← MARKET_RULES.md, ARCHITECTURE.md, REFERENCE_DATA.md, DEPLOYMENT.md, guides/, fr/
├── assets/                   ← style, logo, carte
├── data/market.db            ← base SQLite locale (créée au premier lancement, jamais publiée)
├── CHANGELOG.md, docs/fr/CHANGELOG.md
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

Le formateur dispose d'un jeu de base (Référence 2024, sources publiques) et de quatre variantes pédagogiques (sécheresse hydraulique, ligne Nigeria–Bénin indisponible, gaz cher, forte demande) qui ne modifient qu'un élément, pour la démonstration et la complétion des zones.

Le nouveau front (React, dossier `web/`) se compile avec Node : `cd web && npm install && npm run build`, puis l'API le sert : site vitrine à `/`, hall des salles à `/app`, guides à `/guide/formateur` et `/guide/trader`. Fiche technique de deux pages : [docs/fr/FICHE_TECHNIQUE.md](docs/fr/FICHE_TECHNIQUE.md). Détails dans [docs/fr/ARCHITECTURE.md](docs/fr/ARCHITECTURE.md) ; mise en ligne (nom de domaine, Render, serveur, Docker, HTTPS) dans [docs/fr/DEPLOIEMENT.md](docs/fr/DEPLOIEMENT.md) et, à jour, [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). Site public : https://wapp-dam-simulator.mastereose.fr.

## Tests

```bash
pip install pytest
pytest -q
```

Soixante-six tests, dont ceux qui reproduisent les valeurs du Livrable 2 (welfare 22 317 910 et volume 167 900 MWh sur le cas de référence, 23 082 419 avec blocs, 23 775 223 avec blocs liés et exclusifs) et vérifient les propriétés des prix. Les tests utilisent une base temporaire (`WAPP_DB_PATH`) et ne touchent jamais `data/market.db`.

## Données et confidentialité

- Les NTC et les profils horaires de référence sont des valeurs types estimées pour la formation, pas des données opérationnelles du WAPP. Ils se remplacent depuis la page Administration (NTC) et par les offres des participants.
- Tout fonctionne en local ; la base SQLite reste sur la machine hôte. Ne jamais publier le dossier `data/`.
- Monnaie : libellé paramétrable (USD par défaut), sans effet sur le calcul.
- Le dépôt ne contient ni le logo du WAPP ni la carte du réseau de Tractebel/CEDEAO du Livrable 3 : l'interface utilise une marque neutre (`assets/mark.svg`) et une carte générée à partir de Natural Earth (`assets/network_map.png`, domaine public).

## Auteurs

Kodjovi Plakoo et Enrico Patanè (Mines Paris-PSL, MS OSE 2025). Le simulateur est né d'un projet de groupe du Mastère Spécialisé OSE auquel appartenaient aussi Lucien Kouakou, Mouhamadou Sow et Wissem Hmila. Encadrement : El Hadji Tamsir Diop (SENELEC) et Adrien Atayi (EPEX SPOT).

## Licence

Code sous licence [Apache 2.0](LICENSE). Données de référence et documentation sous [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attributions dans [NOTICE](NOTICE). Simulateur pédagogique indépendant, non affilié au West African Power Pool.

---

## English

The reference version of this README is [README.md](README.md); market rules, architecture, reference data and deployment are documented in English under [docs/](docs/).
