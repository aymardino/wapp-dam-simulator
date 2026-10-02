# Simulateur Day-Ahead WAPP — Audit de l'existant et proposition v2

*Préparé le 2 octobre 2026 pour la discussion avec Tamsir Diop (SENELEC) et Adrien Atayi (EPEX SPOT), suite au message du 27 septembre sur la valorisation du moteur de clearing.*

Base auditée : dossier `wapp_simulator` (livré le 10 avril 2026, Livrable 3) ; tous les constats ci-dessous ont été reproduits par des tests exécutés sur le moteur réel (HiGHS 1.x, Pyomo 6.9.5).

---

## 1. Résumé

- **Le socle est sain** : clearing 24 h sur 14 zones en 0,4 s avec HiGHS, résultats identiques à ceux du livrable (welfare 22,3 M, 167,9 GWh), architecture simple (Streamlit + Pyomo + SQLite) facile à publier.
- **Mais le code ne fait pas tout ce que le livrable et le README annoncent.** Les block orders, offres liées et exclusives sont acceptés par l'interface puis traités comme de simples offres stepwise (pas de MILP, pas de PAB/PRB). L'option « compléter avec les données de référence » ne complète rien. Les NTC ne sont pas modifiables (code mort).
- **Le calcul des prix (P2) donne des prix économiquement incohérents** : des lignes non saturées avec des prix différents aux deux extrémités (93 cas par jour sur le jeu par défaut). Un stagiaire averti le verra tout de suite. Les prix marginaux exacts (duals du LP) sont disponibles gratuitement et corrigent cela.
- **Recommandation** : répondre oui aux trois axes de Tamsir (code ouvert, app web, note technique FR/EN), mais en séquençant : d'abord un lot de correctifs (v1.1), puis une v2 fidèle au livrable (MILP, prix duals, bilingue), puis seulement la publication. Publier l'état actuel exposerait les écarts doc/code.

---

## 2. Ce que je propose de répondre à Tamsir

1. **Oui à la valorisation**, sous trois formes complémentaires :
   - **Code source ouvert** sur GitHub (licence MIT ou Apache-2.0, README FR/EN, citation des auteurs et des encadrants).
   - **Démo web publique** (instance de démonstration) + **instances internes** SENELEC / WAPP déployables en une commande (Docker) pour les vraies formations, ce qui préserve la confidentialité des données saisies.
   - **Note technique ~10 pages FR + EN**, dérivée des livrables 2 et 3 (plan proposé en §6).
2. **Condition** : passer par une v2 avant publication (détail en §4). Estimation : 8 à 10 semaines de travail à temps partiel, découpées en lots livrables séparément.
3. **Points à trancher ensemble** (liste en §7) : licence, hébergement, usage du logo WAPP, qui maintient, calendrier des premières formations.
4. **Disponibilités** : à compléter avant envoi (proposer 2 ou 3 créneaux).

Brouillon de message WhatsApp en §8.

---

## 3. Constats détaillés (tests du 2 octobre 2026)

Gravité : 🔴 fonctionnel (résultat faux ou fonctionnalité annoncée absente) · 🟠 robustesse · 🟡 interface / pédagogie · 🔵 publication.

### 🔴 Fonctionnel

| # | Constat | Preuve | Fichier |
|---|---------|--------|---------|
| 1 | **Block orders, offres liées et exclusives ne sont pas modélisés.** L'UI les enregistre avec un profil texte (`block:8-20`, `linked:...`, `exclusive:...`) que le moteur ne reconnaît pas : repli silencieux sur le profil `baseload`, acceptation partielle autorisée, plage horaire ignorée. Aucune variable binaire dans le moteur. Le livrable 3 (§2.2, §3.2, §5.2) et le README annoncent un MILP et la gestion des PAB/PRB. | Bloc vente NGA 500 MW à 10 €/MWh sur 8h-20h : dispatché 141 MW à 3h du matin (hors plage), partiellement. | `engine/clearing.py:147-155`, `pages/1_Submit_Offers.py:224-233` |
| 2 | **L'option « Utiliser les données de référence (recommandé) » n'applique rien.** Elle est strictement identique à « Ignorer ces zones ». Le message « N zones utiliseront les données calibrées » est faux. | Une seule zone (SEN) soumet : le clearing ne contient que 1 offre + 1 demande (au lieu de 64 + 44), prix 250 €/MWh dans les zones vides. | `pages/3_Admin.py:152-159`, `engine/clearing.py:194-199` |
| 3 | **Les NTC ne sont pas modifiables.** `ntc_override` est lu mais les bornes des flux et la contrainte CIV/GHA/BFA utilisent la constante module `NTC`. Le chemin « NTC depuis la base » importe `get_ntc`, qui n'existe pas dans `db.py` (erreur avalée par `try/except`). | NTC forcées à 0 sur toutes les lignes : 97 564 MWh de flux quand même. | `engine/clearing.py:180-193, 217, 238, 251, 270` |
| 4 | **P2 : règle d'indétermination voulue (Livrable 2 §2.4, recommandation d'Adrien du 13 février), mais ensemble admissible incomplet.** Le principe est le bon : choisir, parmi les prix compatibles avec les quantités, celui qui est le plus proche du milieu de l'intervalle. Mais les contraintes (8)-(12) ne décrivent qu'une partie des prix compatibles : il manque les ordres **rejetés** (vente rejetée ⇒ π ≤ prix, achat rejeté ⇒ π ≥ prix, sinon ordre paradoxalement rejeté) et la règle « ligne non saturée ⇒ prix égaux » (plus le multiplicateur de la contrainte α). Résultat : rente de congestion fictive et prix différents entre zones couplées sans congestion. Correctif : garder l'objectif et le prix de référence de P2, compléter ses contraintes (une vingtaine de lignes). Là où le prix est unique (99 % des cas sur le jeu par défaut), P2 complet redonne le prix dual ; là où il y a un intervalle, la règle du milieu s'applique, ce qui est exactement son rôle. | Jeu par défaut : 93 lignes-heures non saturées avec Δprix > 1 €/MWh (ex. NGA→BEN 20h : 481/800 MW, NGA 101 vs BEN 125) ; rente « fictive » 371 k€/jour ; prix hors ensemble admissible dans 169 des 336 couples zone-heure ; **30 ordres simples paradoxalement rejetés** (vendeur rejeté dont le prix est sous le prix de zone, ou acheteur rejeté dont le prix est au-dessus), ce qu'EUPHEMIA interdit pour les ordres horaires ; avec P2 complet sur la même solution : 0 PRO, 0 ligne non saturée à prix différents. Autre symptôme : le LP P1bis a plusieurs optima, et deux constructions du même modèle donnent des prix P2 qui diffèrent jusqu'à 33,5 €/MWh ; avec l'ensemble admissible complet, les prix uniques ne dépendent plus du sommet choisi par le solveur. | `engine/clearing.py:294-342` |
| 5 | **Soumettre des block orders efface les offres stepwise du même trader** (et inversement) : chaque enregistrement supprime toutes les offres `(zone, player)`. Un trader ne peut pas avoir les deux. Côté achat, les blocs perdent même leur plage horaire à l'enregistrement. | Lecture du code. | `engine/db.py:124, 137` |
| 6 | **PAB/PRB et Minimum Income Condition absents** du moteur (le livrable indique « traités dans le moteur mais non exposés »). | Lecture du code. | `engine/clearing.py` |

### 🟠 Robustesse

| # | Constat | Preuve | Fichier |
|---|---------|--------|---------|
| 7 | **Aucun contrôle du statut du solveur** (P1, P1bis, P2). Si P2 est infaisable, l'admin voit une trace Python. Le plafond `P_MAX = 500` n'est appliqué qu'en front. | Offre à 600 €/MWh → `RuntimeError: A feasible solution was not found`. | `engine/clearing.py:241, 280, 342` |
| 7b | **La page Résultats plante sur une installation propre** : `background_gradient` exige `matplotlib`, absent de `requirements.txt`. Comme Streamlit rend tous les onglets, toute la page (prix, flux, dispatch, tableaux) est remplacée par une trace d'erreur. Cela marchait sur nos machines parce qu'Anaconda installe matplotlib. Quiconque suit le README tombera dessus. | Reproduit dans un environnement neuf (venv Python 3.9, `pip install` selon le README). | `pages/2_Results.py:197`, `requirements.txt` |
| 8 | **Un seul trader par zone** dans la table `players` (clé primaire = zone) : le second connecté dans la même zone (ex. SENELEC puis OMVS) écrase le premier dans la liste des participants. Ses offres, elles, subsistent. | Lecture du schéma. | `engine/db.py:55-60` |
| 9 | **Mode « 1 heure » = heure 0 (minuit)** : solaire nul, charge à 55 % de la pointe. Peu parlant en démo ; il faudrait choisir l'heure. | Test horizon=1 : solaire 0 MW. | `engine/clearing.py:176` |
| 10 | **Marché sans demande (ou sans offre) : prix 250 €/MWh partout** avec volume nul (milieu de [0, 500]). À afficher comme « pas d'échange ». | Test offres seules : volume 0, prix 250. | `engine/clearing.py:306-308` |
| 11 | « Réinitialiser le marché » ne purge que le cache du navigateur de l'admin ; les traders revoient leurs anciennes lignes. SQLite sans mode WAL. | Lecture du code. | `pages/3_Admin.py:72`, `engine/db.py:12` |
| 12 | Horizon : `LOAD_WA[t]` planterait pour un horizon > 24 ; profil `flat` affiché comme `peaker` (même vecteur). | Lecture du code. | `engine/clearing.py:162, 354-359` |

### 🟡 Interface et pédagogie

| # | Constat | Fichier |
|---|---------|---------|
| 13 | **Courbe « Demande acceptée » blanche sur fond blanc** (invisible) dans l'onglet Dispatch ; commentaire « Plotly dark theme » hérité d'un thème sombre. | `pages/2_Results.py:258, 279` |
| 14 | **Devise « EUR / M€ » partout** alors que le marché WAPP est en USD (ou US¢/kWh) : à paramétrer. | toutes les pages |
| 15 | **Interface en français uniquement**, accents supprimés par endroits (« Resultats », « cloture »). Le WAPP compte 5 pays anglophones : bilinguisme FR/EN indispensable pour la diffusion. | toutes les pages |
| 16 | **Pas de vue « mon résultat » pour le trader** (volume accepté, revenu ou coût, prix de sa zone, offres rejetées). C'est pourtant le cœur de la pédagogie. | `pages/2_Results.py` |
| 17 | Pas de décomposition du welfare (surplus consommateur, surplus producteur, rente de congestion) ni de prix/flux sur la carte (PNG statique). | `pages/2_Results.py` |
| 18 | Rafraîchissement automatique par `time.sleep(10)` : bloque la page ; préférer `st.fragment(run_every=...)`. | `pages/2_Results.py:49-54` |

### 🔵 Publication (code ouvert / app web)

| # | Constat |
|---|---------|
| 19 | Mot de passe admin en clair dans le code **et affiché dans l'interface** ; protection XSRF et CORS désactivées. Acceptable en LAN, pas pour une app publique. |
| 20 | **Un seul marché global** dans la base : en app web publique, tous les visiteurs partageraient la même session. Il faut des « salles » (code de session par formation) et une base persistante. |
| 21 | Pas de dépôt git, pas de tests automatisés, pas de Dockerfile, pas de licence. Les NTC « estimées » ne portent aucun avertissement dans l'app. Usage du logo WAPP à faire valider. |

---

## 4. Proposition v2, en quatre lots

### Lot 0 — Correctifs v1.1 (1 à 2 semaines) — *peut démarrer immédiatement*
- Corriger #2 (fusion données de référence pour zones manquantes), #3 (NTC éditables + import CSV), #5, #7 (statuts solveur, erreurs lisibles, `P_MAX` côté moteur), #8 (clé `(zone, player)`), #9 (choix de l'heure en mode 1 h), #10, #11, #12, #13, #14.
- Dépôt git, tests automatisés sur les 5 cas-tests du Livrable 2, `Dockerfile`.

### Lot 1 — Moteur fidèle au livrable (2 à 3 semaines)
- **Ordres bloc / liés / exclusifs réels** : stockage structuré (type, heures, parent, groupe) et MILP (une binaire par bloc, contraintes parent-enfant et exclusivité). **Le MILP existe déjà dans le notebook d'origine** (`wapp_market_clearing_final1.ipynb`, cellules 32-34 et 39-40, résultats Gurobi du Livrable 2 §6) : c'est un portage, pas une réécriture. Restent à écrire : la boucle itérative de correction PAB/PRB du Livrable 2 §3.3 (le notebook détecte et affiche, mais ne relance pas), le P2 et la détection PAB/PRB pour le step 5 (absents du notebook), et la MIC.
- **P2 complété** : même objectif et même prix de référence que le Livrable 2, avec l'ensemble admissible complet (ordres rejetés, égalité des prix sur les lignes non saturées, contrainte α). Les binaires des blocs restent des paramètres fixés, comme prévu au Livrable 2 §3.1. Départage P1bis en lexicographique exact plutôt qu'avec une tolérance absolue de 0,01, qui produit une solution que plus aucun prix ne supporte exactement.
- **PAB/PRB** : détection des blocs paradoxalement acceptés et boucle de rejet (EUPHEMIA simplifié) ; affichage pédagogique. MIC en option si le temps le permet.
- Décomposition du welfare par zone : surplus consommateur, surplus producteur, rente de congestion par ligne.

### Lot 2 — Interface de formation (2 à 3 semaines)
- Bilingue FR/EN (dictionnaire + bascule dans la barre latérale), devise paramétrable.
- Vue « mon résultat » par trader ; carte avec prix et flux par heure ; scénarios pré-enregistrés (sécheresse hydro, indisponibilité d'une ligne, hausse du gaz) ; export Excel.
- Avertissement visible sur les données (NTC estimées, profils types).

### Lot 3 — Publication (2 semaines)
- GitHub public (licence, README FR/EN, citation), démo web, salles de session par code, mot de passe admin via secrets, Docker pour instances internes.
- Note technique FR/EN (§6).

### Options d'hébergement

| Option | Coût | Avantages | Limites |
|--------|------|-----------|---------|
| Streamlit Community Cloud | gratuit | Déploiement depuis GitHub en 5 min, URL publique | 1 Go RAM, mise en veille, fichiers éphémères (SQLite remis à zéro) → démo seulement, ou base externe (Postgres gratuit type Supabase) |
| Hugging Face Spaces | gratuit (stockage persistant ~5 $/mois) | Idem, bonne visibilité | Idem |
| VPS (OVH, Hetzner) ou serveur SENELEC / WAPP + Docker | 5 à 10 €/mois ou interne | Données en interne, contrôle total, plusieurs formations en parallèle | Un administrateur à désigner |

**Recommandation** : code ouvert + démo publique sur Community Cloud + instances internes Docker pour les formations réelles.

---

## 5. Points techniques à discuter avec Adrien

- Complément des contraintes de P2 (ordres rejetés, lignes non saturées) : P2 reste la règle d'indétermination convenue le 13 février ; il s'agit seulement de décrire complètement l'ensemble des prix admissibles avant d'y choisir le prix le plus proche du milieu.
- Règle de traitement des PAB (rejet itératif vs. tolérance) et de la MIC.
- Jeu de données de référence : conserver les valeurs actuelles avec disclaimer, ou attendre les NTC officielles du WAPP ICC.

---

## 6. Note technique FR/EN — plan proposé (≈10 pages)

1. Contexte et objectifs (1 p.) — marché day-ahead WAPP, phase pilote, vocation formation.
2. Marché zonal et couplage par NTC, rappel EUPHEMIA (1,5 p.).
3. Modèle mathématique : P1 welfare, P1bis volume, prix marginaux, flux signés, contrainte CIV/GHA/BFA (2 p.).
4. Types d'ordres : stepwise, bloc, liés, exclusifs, PAB/PRB (1 p.).
5. Architecture logicielle et données (1 p.).
6. Déroulé d'une session de formation et lecture des résultats sur le cas par défaut (2 p.).
7. Limites et données (0,5 p.).
8. Installation, déploiement, licence (1 p.).

---

## 7. Questions à trancher en réunion

1. Code ouvert (quelle licence) ou application web seulement ?
2. Hébergement : SENELEC, WAPP ICC, cloud public ? Qui administre ?
3. Nom du produit, usage du logo WAPP, besoin d'un accord du WAPP ?
4. Qui maintient après la v2 (Mines, EPEX, SENELEC, communauté) ? Crédit des auteurs.
5. Calendrier : première formation interne SENELEC visée ? Cela fixe l'ordre des lots.
6. Données réelles (NTC, profils) : disponibles ou disclaimer ?

---

## 8. Brouillon de réponse WhatsApp

> Bonjour Tamsir, merci pour la proposition, je suis partant. Je viens de refaire un audit de l'outil : le socle est solide (clearing 24 h en moins d'une seconde) mais il y a un lot de corrections à faire avant toute diffusion (block orders pas encore réellement traités par le moteur, prix zonaux à passer sur les prix marginaux, NTC non modifiables, bilinguisme FR/EN). Je propose une v2 en quatre lots : correctifs, moteur complet (MILP, PAB/PRB), interface bilingue avec vue par trader, puis publication (GitHub + démo web + instances internes SENELEC/WAPP) accompagnée de la note technique FR/EN. Je t'envoie le détail par mail. Pour la réunion à trois avec Adrien, je suis disponible [créneau 1], [créneau 2] ou [créneau 3].
