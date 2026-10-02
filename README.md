# WAPP Day-Ahead Market Simulator

**Outil de formation au marché électrique Day-Ahead du West African Power Pool**
Projet MS OSE 2025 — Mines Paris-PSL × SENELEC × EPEX SPOT

---

## Prérequis

- Python 3.10+
- Un solveur LP (voir ci-dessous)

```bash
pip install streamlit pyomo plotly pandas numpy highspy
```

**Solveurs supportés (ordre de priorité automatique) :**
| Solveur | Installation | Recommandé |
|---------|-------------|------------|
| Gurobi  | Licence académique gratuite sur gurobi.com | Oui (le plus rapide) |
| HiGHS   | `pip install highspy` | Oui (gratuit, ~0.5s sur 24h) |
| GLPK    | `conda install -c conda-forge glpk` | Dépannage |
| CBC     | `conda install -c conda-forge coincbc` | Dépannage |

---

## Lancement

### Sur Windows (double-clic)
```
run.bat
```

### Sur Windows (PowerShell)
```powershell
cd wapp_simulator
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### Sur Linux / Mac
```bash
chmod +x run.sh && ./run.sh
```

L'application s'ouvre dans le navigateur sur `http://localhost:8501`.

---

## Accès multi-utilisateurs (formation en présentiel)

### Problème : le firewall bloque le port 8501

Sur un PC d'université ou d'entreprise, les autres participants ne peuvent
généralement pas accéder à `http://[votre-IP]:8501` à cause du firewall réseau.

### Solution : tunnel SSH via localhost.run (sans installation, sans droits admin)

**Étape 1 — Lancer l'application normalement :**
```powershell
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

**Étape 2 — Dans un second terminal PowerShell, ouvrir le tunnel :**
```powershell
ssh -R 80:localhost:8501 nokey@localhost.run
```

**Étape 3 — Copier l'URL générée :**
```
https://xxxxxxxx.lhr.life   ← partager cette URL aux participants
```

Les participants accèdent à l'outil depuis n'importe quel réseau (WiFi, 4G, câble)
via cette URL HTTPS. Aucune installation requise côté participants — juste un navigateur.

> **Note :** L'URL change à chaque nouvelle connexion SSH.
> L'erreur SSL `net_error -200` dans PowerShell est normale et sans conséquence —
> elle indique juste que Streamlit ne peut pas contacter ses serveurs de stats.

### Alternative : ngrok

```powershell
# Télécharger ngrok.exe depuis https://ngrok.com/download (pas d'installation)
.\ngrok.exe http 8501
```

---

## Architecture du projet

```
wapp_simulator/
├── app.py                    ← Accueil : logo WAPP, carte réseau, liste participants
├── pages/
│   ├── 1_Submit_Offers.py   ← Soumission des offres (stepwise / block / linked)
│   ├── 2_Results.py          ← Résultats : prix, flux, dispatch, heatmap
│   └── 3_Admin.py            ← Administration : clearing, phase, paramètres
├── engine/
│   ├── clearing.py           ← Moteur P1/P1bis/P2 (Pyomo, flux signés)
│   ├── db.py                 ← État partagé SQLite (offres, résultats, phase)
│   ├── actors.py             ← Liste des acteurs prédéfinis par zone
│   └── __init__.py
├── assets/
│   ├── style.css             ← Thème clair blanc/vert/orange
│   ├── wapp_logo.png
│   └── wapp_map.png
├── data/
│   └── market.db             ← Base SQLite (créée automatiquement au premier lancement)
├── requirements.txt
├── run.bat                   ← Lanceur Windows
└── run.sh                    ← Lanceur Linux/Mac
```

---

## Modèle économique : décomposition P1/P1bis/P2

| Étape | Problème | Type | Variables | Résultat |
|-------|----------|------|-----------|----------|
| 1 | P1 — Welfare | LP | xs, xd, f | W* |
| 2 | P1bis — Volume | LP | xs, xd, f | x*, f* |
| 3 | P2 — Pricing | LP | π | π*_z,t |

**Flux signés :** une seule variable `f[u,v,t] ∈ [-NTC, +NTC]` par interconnexion,
éliminant les variables binaires de direction (LP pur, steps 1–3).

**Zones modélisées :** 14 pays CEDEAO
`NGA · BEN · TGO · GHA · CIV · BFA · MLI · SEN · GIN · SLE · LBR · GNB · GMB · NER`

**Interconnexions :** 15 paires avec NTC estimés (330 kV et 225 kV)

**Contrainte d'interdépendance :**
`f[GHA→BFA] + f[CIV→BFA] ≤ 0.7 × (NTC_GHA_BFA + NTC_CIV_BFA)`

---

## Types d'ordres disponibles

| Type | Description | Modèle |
|------|-------------|--------|
| **Stepwise** | Segments prix/quantité, acceptation partielle possible | LP |
| **Block Orders** | Fill-or-kill sur une plage horaire | MILP (variable binaire) |
| **Linked** | Bloc enfant conditionné à l'acceptation du parent | MILP |
| **Exclusifs** | Au plus une option d'un groupe acceptée | MILP |

Tous les types supportent les offres de **vente (production)** et d'**achat (demande)**.

---

## Scénario de formation type

1. **Formateur** lance `run.bat`, puis ouvre le tunnel `localhost.run` et partage l'URL
2. **Participants** ouvrent l'URL dans leur navigateur
3. **Connexion** : chaque trader sélectionne son pays et son organisation
4. **Soumission** : chaque trader soumet ses offres (type au choix)
5. **Clearing** : le formateur déclenche le clearing depuis Admin (mot de passe : `<mot-de-passe-retire>`)
6. **Analyse** : tous visualisent les résultats en temps réel (prix, flux, welfare)

---

## Mot de passe administrateur

Défaut : `<mot-de-passe-retire>`
À modifier dans `pages/3_Admin.py` → variable `ADMIN_PASSWORD`

---

## Confidentialité

- Tout fonctionne **localement** — la base SQLite reste sur la machine hôte
- Le tunnel `localhost.run` est chiffré HTTPS mais les données transitent par leurs serveurs
- Pour une confidentialité totale, utiliser uniquement en réseau local (sans tunnel)
- Ne jamais pousser le dossier `data/` sur un dépôt git public

---

*Encadré par El Hadji Tamsir DIOP (SENELEC) et Adrien ATAYI (EPEX SPOT)*
