# Fiche technique — WAPP DAM Simulator

*Version 2.0, octobre 2026. Version anglaise de référence : [TECHNICAL_SHEET.md](../TECHNICAL_SHEET.md).*

| | |
|---|---|
| **Nom** | WAPP DAM Simulator — simulateur de marché day-ahead du West African Power Pool |
| **Nature** | implémentation ouverte de référence du couplage de marché zonal, avec salles de formation multi-participants |
| **Site** | https://wapp-dam-simulator.org |
| **Code source** | https://github.com/aymardino/wapp-dam-simulator |
| **Licence** | Apache 2.0 (code) ; CC BY 4.0 (données de référence et documentation) |
| **Auteurs** | Kodjovi Plakoo, Enrico Patanè (Mines Paris-PSL, Mastère Spécialisé OSE 2025) ; encadrement El Hadji Tamsir Diop (SENELEC) et Adrien Atayi (EPEX SPOT) |
| **Statut** | simulateur pédagogique indépendant, non affilié au WAPP ni à aucun fournisseur de plateforme |

## 1. Ce que fait l'outil

Les participants représentent chacun un pays du WAPP, déposent leurs offres de vente et d'achat pour chaque heure du lendemain, et le formateur lance le clearing. Le moteur répond à trois questions, dans l'ordre : **qui échange** (la combinaison d'échanges qui crée le plus de valeur sans dépasser la capacité des lignes), **comment départager** les solutions équivalentes (le plus d'énergie échangée), **à quel prix** (un prix par pays et par heure, choisi dans l'ensemble complet des prix compatibles avec les quantités). Chaque règle est écrite dans un document public et vérifiée par des tests automatiques.

Trois usages : **former** (séance de marché en trois manches, un pays par participant), **étudier** (cas-test public, règles écrites, moteur ouvert), **comparer** (rejouer un cas, confronter les résultats à ceux d'une autre plateforme, discuter des règles de départage avant le lancement du marché).

## 2. Périmètre fonctionnel

| Élément | Contenu |
|---|---|
| Zones | 14 (NGA, BEN, TGO, GHA, CIV, BFA, MLI, SEN, GIN, SLE, LBR, GNB, GMB, NER) |
| Réseau | 15 interconnexions, capacités de transfert nettes (NTC) par sens, flux signés, approche zonale sans flow-based ; contrainte d'interdépendance sur les deux lignes vers le Burkina Faso (α = 0,7) |
| Horizon | journée J+1 en 24 pas horaires, ou tout sous-ensemble d'heures (mode une heure pour la formation) |
| Ordres | segments prix-quantité (4 par acteur au plus) à profil horaire (solaire, hydraulique, base, pointe, constant, personnalisé) ; blocs tout-ou-rien ; blocs liés (enfant ⇒ parent) ; groupes exclusifs (au plus une option) ; conditions de revenu minimum (terme fixe + terme variable × volume) |
| Bornes de prix | 0 à 500 par MWh (paramètre du modèle) ; libellé de monnaie paramétrable, sans effet sur le calcul |
| Acteurs non joués | trois modes de complétion : acteurs de fond du scénario (défaut), zones sans soumission, aucune complétion |

## 3. Règles de clearing

| Étape | Question | Règle |
|---|---|---|
| P1 | Qui échange ? | maximisation du welfare sous équilibre de chaque zone, bornes de flux, contrainte α, liaisons de blocs ; programme linéaire, en nombres entiers avec blocs (écart 10⁻⁶) |
| P1bis | Comment départager ? | volume maximal à welfare optimal **exact** ; puis partage explicite des offres au même prix : prorata (défaut), ordre de soumission, ou solveur |
| P2 | À quel prix ? | ensemble **complet** des prix admissibles (conditions d'équilibre sur les ordres acceptés, partiels et rejetés, égalité des prix sur les lignes non saturées, inégalité dans le sens de la saturation, contrainte α, bornes) ; prix retenu le plus proche du milieu de l'intervalle admissible local |
| Blocs paradoxaux | | bloc accepté à perte : rejeté et calcul relancé (règle EUPHEMIA, défaut) ; bloc rejeté qui aurait été rentable : toléré et signalé ; règles alternatives disponibles pour comparaison |
| Condition de revenu minimum | | recette insuffisante : retrait de toutes les offres de l'acteur et relance complète |

Diagnostics publiés à chaque clearing : ordres simples paradoxalement rejetés ou acceptés (attendu 0), écarts de prix sur lignes non saturées (attendu 0), écart maximal aux conditions d'équilibre, mode de départage, itérations, identité welfare = surplus consommateur + surplus producteur + rente de congestion.

## 4. Entrées et sorties

| | |
|---|---|
| **Entrées** | carnets d'ordres par participant (interface web, API REST ou fichiers CSV) ; scénario de fond ; capacités d'échange éditables par salle ; heures simulées ; règles |
| **Sorties** | prix par zone et par heure ; flux signés par ligne ; dispatch par profil ; résultat par acteur (volume offert et accepté, prix moyen, recette ou paiement, surplus, offres rejetées) ; décomposition par zone (surplus, position nette, heures sans échange) ; rente de congestion et heures saturées par ligne ; statut des blocs et des conditions ; diagnostics ; exports CSV et JSON |

## 5. Données fournies

| Jeu | Contenu | Fiabilité |
|---|---|---|
| Référence 2024 (défaut) | capacités disponibles, principales centrales et pointes de demande par pays, capacités des lignes, coûts par technologie, d'après des sources publiques 2023-2025 | sourcé pour les capacités et plusieurs lignes ; **estimé** pour plusieurs pointes et capacités (signalées) ; **hypothèse** pour les prix des offres (coût variable typique) |
| Quatre variantes pédagogiques | sécheresse hydraulique, ligne Nigeria–Bénin indisponible, gaz cher, forte demande : une seule chose change par rapport au jeu de base | dérivées du jeu 2024 |
| Jeu de test | données synthétiques du projet, valeurs de non-régression (welfare 22 317 910, volume 167 900 MWh) | réservé aux tests |

Les prix produits sont des résultats de simulation sur ces données, pas des prix observés : le marché day-ahead du WAPP n'a pas encore démarré. Détail et sources : `docs/REFERENCE_DATA.md`.

## 6. Architecture technique

| Couche | Technologie |
|---|---|
| Moteur | Python 3.10+, modèles Pyomo, solveur libre HiGHS inclus ; Gurobi utilisé automatiquement s'il est installé |
| API | FastAPI, SQLAlchemy (SQLite par défaut, PostgreSQL possible), documentation interactive sur `/docs`, flux d'événements temps réel (Server-Sent Events) |
| Interface | React, Vite, TypeScript, Tailwind ; page publique, hall, salle de marché, poste du formateur ; bilingue FR/EN ; cartes Natural Earth (domaine public) |
| Ligne de commande | `python -m engine.cli` : CSV en entrée, JSON et CSV des prix en sortie |
| Application historique | Streamlit, conservée pour la formation locale |

## 7. Performance

| Cas | Temps |
|---|---|
| Référence 2024, 24 h, 14 zones, 80 segments (3 000 variables continues) | 0,4 s |
| 150 ordres bloc avec boucle de blocs paradoxaux | ≈ 11 s |
| Salle de formation de 20 participants | 2 vCPU et 4 Go suffisent |

## 8. Qualité et vérification

- 66 tests automatiques exécutés à chaque modification (intégration continue) : valeurs de non-régression, règles de blocs et de conditions, API, ligne de commande.
- Campagne de cas aléatoires (segments, blocs simples, liés, exclusifs, conditions, toutes les règles, 24 h ou une heure, capacités réduites) contrôlée par un vérificateur indépendant du solveur : prix dans les bornes, flux dans les capacités, équilibre horaire, positions nettes de somme nulle, accepté ≤ offert, règles de blocs, conditions satisfaites ou retirées, identité du welfare.
- Reproduction en trois commandes (voir `README.md`).

## 9. Déploiement et exploitation

| | |
|---|---|
| **Image** | une image Docker (API + interface compilée), `Dockerfile.app` |
| **Hébergement** | Render en un clic (`render.yaml`, disque persistant) ou serveur virtuel avec `docker-compose.yml` et HTTPS automatique (Caddy) ; poste local ou réseau de formation sans Internet également possibles |
| **Accès** | pas de comptes : une salle a un code à six caractères, chaque participant un jeton ; aucune donnée personnelle hormis le nom d'organisation saisi |
| **Garde-fous** | purge des salles inactives (30 jours), quota de création par adresse (20 par jour), origines autorisées configurables |
| **Données** | base SQLite locale ou volume persistant ; sauvegardes par script ; aucune donnée opérationnelle du WAPP |

## 10. Limites

Non modélisés : pertes, réserves, rampes et durées minimales, contraintes flow-based, enchères intrajournalières, règlement financier, arrondi des prix publiés, conditions de revenu minimum côté achat. Données 2024 à valider avec le centre de coordination du WAPP et les compagnies (pointes, capacités d'échange, coûts).

## 11. Feuille de route

| Échéance | Étape |
|---|---|
| Octobre 2026 | mise en ligne sous nom de domaine, organisation GitHub, validation des données avec SENELEC |
| Mi-novembre 2026 | note technique (working paper) et cas-tests publics ; campagne de comparaison proposée au centre de coordination |
| Décembre 2026 | première formation sur le site en ligne |
| 1er janvier 2027 | lancement prévu du marché day-ahead du WAPP |

## 12. Citation suggérée

Plakoo K., Patanè E. (2026). *WAPP DAM Simulator : implémentation ouverte de référence du couplage de marché day-ahead zonal pour le West African Power Pool*, version 2.0. https://github.com/aymardino/wapp-dam-simulator
