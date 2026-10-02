# Journal des modifications

Toutes les modifications notables du simulateur sont consignées ici, de la plus récente à la plus ancienne.
Chaque entrée renvoie au commit git correspondant (`git log`).

## [2.0.0-dev] — octobre 2026

### Étape 12 — Site vitrine, kit de mise en ligne, nettoyage avant publication

**Ajouté**
- Page d'accueil publique bilingue (`web/src/pages/Landing.tsx`, route `/` ; le hall des salles passe à `/app`) :
  présentation, carte vivante du cas de référence 2024 calculée par le moteur (heure animée, prix et flux,
  welfare, volume, lignes saturées, temps de calcul), prix horaires des 14 zones, les trois programmes
  P1 / P1bis / P2 en langage courant, contenu du simulateur, publics visés, section « ouvert et vérifiable »,
  avertissements (simulateur indépendant non affilié au WAPP, données reconstituées et NTC estimées), auteurs,
  liens vers les guides, le dépôt et la note technique (`web/src/links.ts`, à renseigner à la publication).
- `GET /api/v1/demo` : clearing du scénario Référence 2024 mis en cache pour le site (test `test_demo_endpoint_is_cached`).
- Kit de mise en ligne : `.env.example` (domaine, CORS, purge, quota), `deploy/setup_server.sh` (installation
  d'un serveur Ubuntu : Docker, pare-feu, clone, démarrage), `deploy/update.sh`, `deploy/backup.sh` ;
  `Caddyfile` paramétré par `DOMAIN` avec en-têtes de sécurité et redirection www ; image `Dockerfile.app`
  sans privilèges (utilisateur dédié), contrôle de santé, en-têtes de proxy ; `docs/DEPLOIEMENT.md` réécrit
  (achats, publication GitHub, installation, exploitation, liste de contrôle avant annonce).
- Intégration continue : compilation du front (Node 20) en plus des tests Python.
- Métadonnées de la page (titre, description, Open Graph) pour le référencement et les partages.

**Modifié**
- Marque neutre `mark.svg` à la place du logo du WAPP dans le front et dans l'application Streamlit ; carte du
  réseau `assets/network_map.png` générée à partir de Natural Earth (domaine public) à la place de la carte
  Tractebel/CEDEAO du Livrable 3. Les deux fichiers d'origine sont retirés du dépôt et de son historique, le
  projet n'étant pas affilié au WAPP et ces images n'étant pas libres de droits.
- À faire par l'auteur avant le premier push (commande dans `docs/DEPLOIEMENT.md`, section 3) : réécrire
  l'historique git pour remplacer l'ancien mot de passe administrateur du Livrable 3, présent dans les deux
  premiers commits (`pages/3_Admin.py`, `README.md`, `Dockerfile`), et retirer les images du WAPP des
  anciens commits.
- Suite : 65 tests.

### Étape 11 — Guides, mode « acteurs de fond », nom de domaine

**Ajouté**
- Guides du formateur et du trader, en français et en anglais (`docs/guides/`), accessibles dans l'application
  (menu Guides du bandeau et liens de l'accueil, pages `/guide/formateur` et `/guide/trader`) : préparation
  d'une séance, déroulé type en trois manches, réglages expliqués, lecture des résultats, questions fréquentes ;
  côté trader, comment déposer chaque type d'ordre et comprendre son résultat.
- Mode de complétion « acteurs de fond » (nouveau défaut des salles) : tous les acteurs du scénario restent dans
  le marché, sauf ceux de la zone d'un participant dont le nom correspond au sien ou à l'un de ses ordres, qui
  sont remplacés. Un nom libre n'efface rien ; un nom choisi dans la liste prend la place de l'acteur réel.
  Les deux autres modes (« zones sans soumission », « aucune ») restent disponibles ; sélecteur avec
  explication dans le poste du formateur, règle décrite dans `docs/REGLES_DE_MARCHE.md`.
- Nom de domaine retenu : wapp-dam-simulator.org (Caddyfile, docker-compose, guide de déploiement).
- Suite : 64 passed in 14.96s.

### Étape 10 — Campagne de simulations, noms de participants, licence

**Ajouté**
- `engine/checks.py` : vérification indépendante d'un résultat (prix dans les bornes, flux dans les NTC, équilibre
  production-demande à chaque heure, somme des positions nettes nulle, accepté ≤ offert, aucun bloc
  paradoxalement accepté, enfant accepté ⇒ parent accepté, au plus une option par groupe exclusif, chaque
  condition de revenu minimum satisfaite ou retirée, identité du welfare).
- `tests/test_properties.py` : cas aléatoires (segments, blocs simples, liés, exclusifs, MIC, règles de prix, de
  blocs et de partage, scénarios, 24 h ou une heure, NTC réduites) vérifiés par ces contrôles ; 25 cas par
  défaut, 150 exécutés avant publication (`WAPP_PROPERTY_CASES=150 pytest`), plus des cas limites.
- Licence Apache 2.0 (`LICENSE`), `NOTICE` avec les attributions et la mention de non-affiliation au WAPP ;
  données et documentation sous CC BY 4.0.
- API : nom de participant unique par salle (insensible à la casse, espaces normalisés), retrait d'un participant
  et de ses ordres par le formateur, suggestions d'organisations par zone dans l'accueil.

**Corrigé (découvert par la campagne)**
- Règle `l2` des blocs paradoxaux : un bloc forcé à l'acceptation parce que paradoxalement rejeté pouvait
  rester paradoxalement accepté aux nouveaux prix ; il est maintenant rejeté définitivement (la règle « pas de
  PAB » prime). Un forçage qui rend le problème infaisable (bloc impossible à absorber) est levé et noté.
- Nombre maximal d'itérations de la boucle PAB calé sur le nombre de blocs (deux changements par bloc au plus).
- Suite : 62 passed in 15.07s.

### Correctifs — lisibilité de la carte et identités multiples

- Carte : nœuds plus petits ; Gambie, Guinée-Bissau, Sierra Leone, Liberia, Togo et Bénin sont déportés vers la
  mer avec un trait de rappel vers leur position réelle, pour ne plus se chevaucher.
- Un même navigateur peut mémoriser plusieurs identités de trader ou d'observateur pour une salle (utile pour
  tester seul) : liste dans « Vos salles » sur l'accueil, sélecteur dans le bandeau de la salle de marché.
  Les liens de bascule formateur / trader n'apparaissent que sur l'appareil qui détient le jeton correspondant.

### Étape 9 — Données de référence sourcées et valeurs par défaut réalistes

**Ajouté**
- Scénario `reference_2024` « Référence 2024 (sources publiques) » : capacités disponibles, pointes de demande,
  coûts par technologie et capacités des lignes d'après des sources publiques 2023-2025, documentés chiffre par
  chiffre dans `docs/DONNEES_DE_REFERENCE.md` avec les estimations signalées. Le jeu du Livrable 2 reste le
  défaut des tests jusqu'à validation par SENELEC et le centre de coordination du WAPP.
- Dans la salle de marché, les quantités et prix proposés pour un nouvel ordre sont tirés des tailles types des
  centrales de la zone (quelques dizaines de MW au Togo ou en Gambie, plusieurs centaines au Nigeria) au lieu
  de 100 MW partout.
- Test de plausibilité du jeu 2024 (35 tests au total).

### Étape 8 — Scénarios, temps réel, export et garde-fous (API et moteur)

**Ajouté**
- `engine/scenarios.py` : cinq scénarios pédagogiques dérivés des données de référence (référence, sécheresse
  hydraulique, ligne Nigeria–Bénin indisponible, gaz cher, forte demande). Le moteur accepte `reference_rows`
  pour substituer ces données à celles du Livrable 2 dans la démonstration et la complétion des zones.
- API : `GET /scenarios`, réglage `scenario` par salle (les NTC du scénario s'appliquent sous celles du
  formateur), `GET /rooms/{code}/results/{id}/prices.csv`, flux d'événements `GET /rooms/{code}/events`
  (Server-Sent Events : état de la salle à chaque changement, battement toutes les 15 s, `?once=true` pour
  un seul état).
- Garde-fous pour une mise en ligne : purge des salles sans activité depuis `WAPP_ROOM_TTL_DAYS` jours
  (30 par défaut) à chaque création, et au plus `WAPP_MAX_ROOMS_PER_IP_PER_DAY` salles par adresse et
  par jour (20 par défaut, réponse 429 au-delà).
- Cinq tests (34 au total).

**Front**
- Graphiques ECharts (rendu SVG) dans la salle de marché et au poste du formateur : prix horaires par zone
  (la zone du trader en gras), dispatch empilé par profil avec la demande acceptée, flux horaires des huit
  corridors principaux avec la NTC en légende. Onglets Carte / Prix / Dispatch / Flux.
- Temps réel : abonnement au flux d'événements de la salle (badge « En direct »), rechargement à chaque
  changement d'état ; repli automatique sur un sondage si le navigateur ne gère pas les événements serveur.
- Sélecteur de scénario avec sa description dans les réglages du formateur ; liens d'export CSV et JSON.

### Correctif — réglages du formateur enregistrés immédiatement

- La case « Compléter les zones sans soumission » n'était prise en compte qu'après un clic sur « Enregistrer » ;
  l'annonce sous le bouton reflétait la case, le clearing utilisait le réglage enregistré, d'où un welfare de
  référence malgré une case décochée. Tous les réglages du poste du formateur sont désormais enregistrés dès
  le changement, et la case est placée à côté du bouton de lancement.
- Frontières des pays en noir sur la carte.
- Rappel de développement : l'API doit être relancée (ou lancée avec `--reload`) après une modification du
  code Python ; le front compilé, lui, est relu à chaque requête.

### Étape 7 — Carte géographique et lisibilité du mode démonstration

**Ajouté**
- Fond de carte d'Afrique de l'Ouest sous le réseau, à partir de Natural Earth (domaine public, résolution 50 m)
  extrait à la compilation par `web/scripts/extract_map.mjs` en un GeoJSON de 86 Ko ; projection Mercator
  (d3-geo), nœuds placés aux coordonnées réelles des pays, pays membres mis en évidence, légende et crédit.
- Le moteur renvoie `summary.reference_zones`, la liste des zones complétées par les données de référence.
  Le poste du formateur annonce avant le calcul combien de zones ont des ordres et ce qu'il adviendra des
  autres ; après le calcul, un bandeau « Démonstration » s'affiche quand aucune offre de participant n'a été
  utilisée, et un badge « Données de référence · N zones » sinon. Même badge dans la salle de marché.

**Modifié**
- L'API refuse (422, message en clair) de lancer un clearing sans aucun ordre quand la complétion par les
  données de référence est désactivée, au lieu de produire un marché vide à 250 par MWh.
- Deux tests ajoutés (29 au total).

### Étape 6 — Première passe de design du front et navigation entre rôles

**Ajouté**
- Système de design v1 : bandeau sombre avec le logo, le nom de la salle, le code et la phase ; panneaux blancs
  à filet fin ; onglets pour le carnet d'ordres (vente, achat, blocs, MIC) avec compteurs ; indicateurs ;
  états vides qui expliquent quoi faire ; corps de texte à 15 px, chiffres en police à chasse fixe.
- Carte du réseau WAPP (`web/src/components/NetworkMap.tsx`) : 14 zones colorées par prix à l'heure choisie,
  15 lignes dont l'épaisseur suit le flux, flèche de sens, lignes saturées en rouge, légende. Affichée dans la
  salle de marché et au poste du formateur.
- Accueil : liste « Vos salles » avec, pour chaque salle mémorisée, l'accès au poste du formateur et à la salle
  de marché ; lien de bascule entre les deux dans le bandeau ; le poste du formateur propose de rejoindre sa
  propre salle comme trader (code prérempli).

**Corrigé**
- Un formateur qui rejoignait sa salle comme trader perdait l'accès à son poste : jetons désormais conservés
  par salle et par rôle, nom de la salle mémorisé.

### Étape 5 — API REST et squelette de la nouvelle application

**Ajouté**
- `api/` : API FastAPI de salles de marché multi-participants (création d'une salle par le formateur, code à
  partager, traders et observateurs avec jeton, carnet d'ordres par trader remplacé à chaque dépôt, paramètres et
  règles par salle, NTC surchargées, lancement du clearing, historique des résultats, résultat individuel).
  Base SQLAlchemy distincte (`data/rooms.db`, ou Postgres via `WAPP_API_DATABASE_URL`). Documentation
  interactive sur `/docs`. Le moteur n'est pas modifié : l'API lui passe les mêmes lignes que Streamlit.
- `engine/cli.py` : ligne de commande du moteur (CSV en entrée, JSON et CSV des prix en sortie).
- `web/` : squelette du nouveau front React (Vite, TypeScript, Tailwind) avec le système de design sobre
  (palette neutre, un accent, deux poids), le bilinguisme, le client API typé et les trois écrans : hall,
  salle de marché du trader, poste du formateur. Non compilé sur cette machine (Node absent) : voir web/README.md.
- `docs/ARCHITECTURE.md` : modèle de données, routes, structure du front, lancement.
- `Dockerfile.app` : image unique API + front compilé.
- Tests `tests/test_api.py` (parcours complet, droits, validations) et `tests/test_cli.py`.
- Front compilé avec Node 24 (TypeScript et Vite sans erreur) et vérifié dans le navigateur sur le parcours
  complet : création d'une salle, trader qui rejoint et dépose ses ordres, clearing lancé par le formateur,
  marché et résultat individuel affichés. Un jeton par salle et par rôle, pour qu'un formateur puisse aussi
  tester comme trader depuis le même navigateur.
- `docs/DEPLOIEMENT.md` (poste, réseau de formation, Internet), `docker-compose.yml` et `Caddyfile`
  (HTTPS automatique derrière un nom de domaine).

### Étape 4 — Règles restantes du Livrable 2 : partage des ex æquo et Minimum Income Condition

**Ajouté**
- Règle explicite de partage entre offres de même zone, même sens, même heure et même prix, appliquée après
  P1bis : `prorata` (défaut), `order` (ordre de soumission) ou `solver`. Le total accepté du groupe, le welfare,
  le volume et l'ensemble des prix admissibles sont inchangés. Réglable dans Administration.
- Minimum Income Condition (Livrable 2 §6.3, annoncée pour le L3) : par acteur vendeur, terme fixe et terme
  variable par MWh ; si la recette aux prix finals est insuffisante, toutes ses offres (et les blocs enfants qui en
  dépendent) sont retirées et la séquence complète est relancée, jusqu'à satisfaction. Table `mic_conditions`,
  saisie dans la page Soumission, état de chaque condition dans les résultats et les diagnostics.
- Résultats par acteur : statut `withdrawn_mic` pour les offres retirées.
- Quatre tests : prorata et ordre de soumission (même welfare, même volume), retrait MIC avec relance et nouveau
  prix, condition satisfaite, retrait des blocs enfants.
- Règles de marché mises à jour (§3 P1bis, nouveau §5 MIC, tolérance MIC_TOL, liste de ce qui reste hors modèle).

### Correctif — base de données héritée (2 octobre 2026, soir)

- Une base créée par une version antérieure du code contenait déjà une table `ntc` avec les colonnes
  `zone_from, zone_to, value_mw` ; `CREATE TABLE IF NOT EXISTS` la laissait en place et la page
  Administration plantait (`no such column: u`). `init_db()` compare désormais les colonnes de chaque table
  à celles attendues : la table `ntc` héritée est convertie, toute autre table incompatible est renommée en
  `<table>_legacy_<horodatage>` sans perte de données, puis la table attendue est créée.
- Les NTC lues en base ne sont signalées comme « modifiées » (note du moteur, bandeau d'administration) que si
  elles diffèrent réellement des valeurs par défaut.
- Tests `tests/test_db.py` : migration d'une base héritée (participants, NTC, table incompatible), idempotence.

### Étape 3 — Documentation et publication

**Ajouté**
- `docs/REGLES_DE_MARCHE.md` : toutes les règles appliquées par le moteur, en toutes lettres (ensemble des prix
  admissibles, prix de référence, départage, blocs paradoxaux, tolérances, ce qui n'est pas modélisé), avec un
  résumé en anglais. Base de la note technique.
- `Dockerfile` et `.dockerignore` ; mot de passe administrateur lu dans `WAPP_ADMIN_PASSWORD` ou
  `.streamlit/secrets.toml`, plus jamais affiché dans l'interface.
- Intégration continue GitHub Actions (`.github/workflows/tests.yml`) : la suite de tests tourne à chaque push.
- README réécrit : installation sans licence Gurobi, déroulé d'une session, architecture, modèle, tests,
  données et confidentialité, auteurs, résumé en anglais.
- Note d'état en tête de `AUDIT_V2.md` indiquant les constats traités.

### Étape 2 — Interface (`app.py`, `ui_common.py`, `pages/`)

**Ajouté**
- Interface bilingue français / anglais : dictionnaire de 265 textes dans `ui_common.py`, sélecteur de langue
  dans la barre latérale de chaque page, langue par défaut réglable par l'administrateur.
- Monnaie paramétrable (libellé, USD par défaut) utilisée dans tous les affichages.
- Page Résultats : onglet **Mon résultat** (volume offert et accepté, taux d'acceptation, recette ou paiement,
  surplus, offres rejetées et explication, prix de la zone), onglet **Ordres bloc** (décision, prix moyen,
  surplus, statut OK / PAB / PRB expliqué, planning), onglet **Analyse** (surplus par zone, rente de congestion
  par ligne, identité du welfare, vérifications de cohérence, règles appliquées), export CSV des prix.
- Page Administration : éditeur de NTC (tableau modifiable, retour aux valeurs par défaut), choix de l'heure
  simulée en mode 1 h, choix de la règle de prix et de la règle de traitement des blocs paradoxaux, aperçu des
  ordres bloc, diagnostics du dernier clearing.
- Page Soumission : éditeur d'ordres bloc structuré (sens, plage horaire, parent, groupe exclusif) à côté des
  offres par segments, sans que l'un efface l'autre ; récapitulatif des blocs de la zone.
- Avertissement visible sur le caractère illustratif des NTC et des profils.

**Corrigé**
- L'option « compléter avec les données de référence » complète réellement les zones sans soumission ;
  l'option « ignorer » donne un marché partiel ; le mode démonstration ignore les soumissions.
- La page Résultats ne dépend plus de matplotlib (barres de saturation natives) et ne plante plus sur une
  installation propre ; la courbe de demande acceptée est visible (trait sombre) ; les heures affichées sont
  celles réellement simulées ; le rafraîchissement automatique utilise `st.fragment` au lieu de bloquer la page.
- Les erreurs de clearing s'affichent en clair (message de `ClearingError`) au lieu d'une trace Python.
- Plusieurs traders d'un même pays apparaissent tous dans la liste des participants.
- Le mot de passe administrateur n'est plus affiché dans la page.

### Étape 1 — Moteur de clearing (`engine/clearing.py`, `engine/db.py`, `tests/`)

**Ajouté**
- Ordres bloc, liés et exclusifs réellement modélisés (MILP, une variable binaire par bloc, contraintes
  parent-enfant et groupe exclusif), portés du notebook `wapp_market_clearing_final1.ipynb` (steps 4 et 5).
  Les blocs sont stockés dans une nouvelle table `block_orders` (zone, trader, nom, sens, MW, prix,
  heure de début, heure de fin, parent, groupe) au lieu d'un texte dans la colonne « profil ».
- Boucle de traitement des blocs paradoxaux (Livrable 2 §3.3). Règle par défaut `euphemia` : les blocs
  paradoxalement acceptés (PAB) sont fixés à 0 et le clearing est relancé ; les blocs paradoxalement
  rejetés (PRB) sont tolérés et signalés. Règle `l2` : PAB fixés à 0 et PRB fixés à 1 (texte du livrable).
  Règle `none` : détection seule.
- NTC modifiables : table `ntc`, fonctions `get_ntc` / `set_ntc` / `reset_ntc`, paramètre `ntc_override`
  réellement appliqué aux bornes des flux et à la contrainte α.
- Heures simulées paramétrables (`hours=[19]` pour une heure de pointe, `range(24)` pour la journée).
- Option `fill_missing_zones` : les zones sans aucune soumission sont complétées par les données de référence.
- Validation des entrées avec messages explicites (`ClearingError`) : zone inconnue, prix hors bornes
  [0, 500], quantité négative, plage horaire invalide, profil inconnu.
- Contrôle du statut du solveur à chaque étape ; plus de trace Python en cas d'infaisabilité.
- Résultats enrichis dans `summary` : résultats par acteur (volume offert et accepté, prix moyen, recette ou
  paiement, surplus, offres rejetées), décomposition par zone (surplus consommateur, surplus producteur,
  position nette, heures sans échange), rente de congestion et heures saturées par ligne, statut des blocs
  (OK, PAB, PRB), règles utilisées, diagnostics de cohérence.
- Suite de tests `tests/test_engine.py` (15 tests) calée sur les valeurs du Livrable 2 : welfare 22 317 910
  et volume 167 900 MWh (step 3), welfare 23 082 419 et 5 blocs acceptés sur 6 (step 4),
  welfare 23 775 223 (step 5).

**Modifié**
- **P2 « complet »** (mode `pricing='complete'`, par défaut). L'objectif et le prix de référence du
  Livrable 2 §2.4 sont conservés (prix le plus proche du milieu de l'intervalle admissible), mais
  l'ensemble des prix admissibles est maintenant décrit par les conditions KKT complètes :
  vente rejetée ⇒ prix ≤ offre, achat rejeté ⇒ prix ≥ offre, ligne non saturée ⇒ prix égaux des deux
  côtés, multiplicateur explicite pour la contrainte d'interdépendance α. Sur le jeu de données de
  référence, cela supprime 30 ordres simples paradoxalement rejetés et 74 écarts de prix sans congestion.
  Le mode `pricing='l2'` conserve exactement les contraintes (8)-(12) du Livrable 2 pour comparaison.
- Prix de référence : les ordres rejetés resserrent l'intervalle (vente rejetée = borne haute, achat
  rejeté = borne basse), ce qui donne un prix cohérent dans les zones sans échange au lieu de 250.
- **P1bis exact** : la contrainte de welfare passe de `W ≥ W* − 0,01` à `W ≥ W*`. La tolérance absolue
  était entièrement consommée par la maximisation du volume et produisait une solution que plus aucun
  prix ne supportait. Si le solveur ne trouve pas de solution à P1bis, la solution de P1 est conservée
  et signalée dans les diagnostics (`tie_break`).
- Seuils de classification des ordres : `X_TOL = 1e-4` (au lieu de 0,01 / 0,99) et `F_TOL = 1e-3 MW`.
- Dispatch : le profil est lu depuis le nom stocké en base (plus de confusion `flat` / `peaker`), et
  les blocs de vente acceptés apparaissent dans une catégorie `block`.
- Participants : clé primaire `(zone, trader)` ; deux organisations d'un même pays peuvent être
  connectées simultanément. Migration automatique de l'ancienne table.
- SQLite en mode WAL ; chemin de la base configurable par la variable d'environnement `WAPP_DB_PATH`
  (utilisée par les tests pour ne jamais toucher `data/market.db`).
- Paramètres de session ajoutés : `hour`, `currency`, `lang`, `pricing`, `pab_rule`, `fill_missing`.

**Supprimé**
- L'import mort `from engine.db import get_ntc` dans un `try/except` silencieux (la fonction existe désormais).

### Étape 0 — Point de départ
- Dépôt git initialisé sur l'état livré le 10 avril 2026 ; `data/` exclu du suivi.
- Audit des anomalies (`AUDIT_V2.md`) et plan de valorisation (`PLAN_VALORISATION.md`).
