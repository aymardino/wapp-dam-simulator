# Journal des modifications

Toutes les modifications notables du simulateur sont consignées ici, de la plus récente à la plus ancienne.
Chaque entrée renvoie au commit git correspondant (`git log`).

## [2.0.0-dev] — octobre 2026

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
