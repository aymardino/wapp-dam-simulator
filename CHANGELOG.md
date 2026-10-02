# Journal des modifications

Toutes les modifications notables du simulateur sont consignées ici, de la plus récente à la plus ancienne.
Chaque entrée renvoie au commit git correspondant (`git log`).

## [2.0.0-dev] — octobre 2026

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
