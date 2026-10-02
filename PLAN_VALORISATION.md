# Plan de valorisation du simulateur Day-Ahead WAPP

*Rédigé le 2 octobre 2026 à partir des notes de la réunion avec Tamsir Diop (SENELEC) et Adrien Atayi (EPEX SPOT). Complète l'audit technique [AUDIT_V2.md](AUDIT_V2.md).*

---

## 1. Ce qui ressort de la réunion

- **Objectif** : mettre en accès ouvert le fonctionnement du clearing, les produits (offres simples, blocs, liées, exclusives), la manière de l'utiliser et de le faire tourner avec d'autres données. Rendre le module opérationnel pour un tiers.
- **Publier vite** : note technique, article ou working paper, puis diffusion LinkedIn et site hébergé. Le marché Day-Ahead du WAPP doit démarrer au plus tard le 1er janvier 2027.
- **Contexte concurrentiel** : le WAPP dispose déjà d'une plateforme en mode pilote depuis trois ans, réservée aux acteurs, fournie par General Electric. Côté public, GE Vernova confirme avoir déployé dans l'ICC d'Abomey-Calavi (Bénin) son logiciel GridOS avec un EMS, un WAMS et un « Advanced Market Management System ». C'est une boîte noire commerciale : même au WAPP, personne ne sait comment elle tranche les cas d'indétermination. Notre outil devient une **implémentation ouverte de référence** qui permet de poser ces questions.
- **Site** : plus professionnel, design moderne, sortir de Streamlit si possible.
- **Question ouverte** : héberger sous le domaine de Mines Paris (projet externe) ou acheter un nom de domaine.

---

## 2. Positionnement proposé

« Implémentation ouverte de référence du couplage de marché day-ahead zonal appliqué au WAPP » : code source, formulation mathématique, règles de prix et de départage documentées, jeu de cas-tests publics et interface de formation. Ce n'est pas un concurrent du MMS de GE Vernova, c'est l'outil qui dit ce qu'un marché zonal **devrait** produire sur un cas donné, et qui permet de le vérifier.

Nom de produit : éviter d'utiliser « WAPP » seul sans accord (acronyme et logo appartiennent à l'organisation). Pistes neutres à vérifier sur un registrar (le whois est bloqué depuis cette machine) : `wappsim.org`, `openwapp.org`, `wa-dam.org`. À valider avec Tamsir, qui peut sonder le WAPP.

---

## 3. L'angle scientifique : les cas d'indétermination

C'est le point d'attaque retenu en réunion. Chiffres mesurés sur notre moteur, jeu de données par défaut, 14 zones, 24 heures (336 couples zone-heure) :

| Mesure | Résultat |
|--------|----------|
| Zone-heures où le prix d'équilibre n'est pas unique (intervalle admissible non réduit à un point) | 3 sur 336, largeur jusqu'à 30 $/MWh (BEN 1 h : [48, 78]) |
| Groupes d'offres au même prix, même zone, même heure, avec partage de volume non trivial (indétermination de volume) | 5 |
| Prix P2 actuels de l'app situés **hors** de l'ensemble des prix admissibles | 169 sur 336, soit 50 % |
| Ordres simples paradoxalement rejetés sous les prix P2 actuels (interdits dans EUPHEMIA pour les ordres horaires) | 30 ; 0 avec P2 complété |
| Solution P1bis (départage par volume, tolérance absolue 0,01) | consomme exactement la tolérance et n'est plus supportée par aucun prix d'équilibre exact ; plusieurs optima, prix P2 qui varient jusqu'à 33,5 $/MWh selon le sommet choisi par le solveur |

Lecture : sur un cas réaliste, l'indétermination de prix est rare mais réelle, l'indétermination de volume existe, et surtout **la règle de prix doit être formulée comme une sélection dans l'ensemble des prix admissibles** (conditions de Karush-Kuhn-Tucker complètes, réseau compris). P2 est exactement cette règle, telle que recommandée par Adrien le 13 février 2026 (Livrable 2 §2.4) ; il faut seulement compléter ses contraintes (ordres rejetés, lignes non saturées, contrainte α) pour que l'ensemble dans lequel il choisit soit le bon. Le MMS de GE ne dit pas ce qu'il fait. C'est exactement la question à poser au WAPP.

Catalogue de cas d'indétermination à documenter et à tester dans le working paper :

1. Courbes offre et demande qui se croisent sur un segment vertical : intervalle de prix. Règle candidate : milieu de l'intervalle (pratique EUPHEMIA documentée), à comparer avec borne basse ou haute.
2. Offres au même prix : partage du volume. Règles candidates : prorata des quantités, priorité temporelle, maximisation du volume, aléatoire.
3. Zone sans échange, prix au plafond ou au plancher.
4. Ligne non saturée entre deux zones : égalité des prix obligatoire. Contrainte d'interdépendance CIV/GHA/BFA : écart de prix sans saturation individuelle.
5. Ordres bloc : blocs paradoxalement acceptés (interdits dans EUPHEMIA) et paradoxalement rejetés (tolérés), optima multiples du MILP, absence de prix supportant la solution.
6. Ordres liés et exclusifs : mêmes questions, cas de non-existence.
7. Flux dégénérés : plusieurs répartitions de flux pour les mêmes prix (boucles).
8. Tolérances et arrondis : à quel pas le MMS arrondit-il prix et volumes, et avant ou après le départage ?

Livrable associé : **suite de cas-tests publics** (entrées JSON, résultats attendus sous règles explicites). Le WAPP ou l'ERERA peuvent faire tourner les mêmes cas sur le MMS et comparer. C'est la façon concrète et non conflictuelle de « challenger » la boîte noire.

Corrections à faire dans notre moteur pour être crédibles sur ce terrain :
- P2 conservé (objectif et prix de référence du Livrable 2) avec l'ensemble admissible complet : ordres rejetés, égalité des prix sur les lignes non saturées, multiplicateur de la contrainte α ;
- départage lexicographique exact (pas de tolérance absolue sur le welfare) ;
- MILP réel pour blocs, liés, exclusifs, avec détection des blocs paradoxaux ;
- règle explicite de partage des offres à prix égal.

---

## 4. Publication : quoi, où, quand

| Étape | Quoi | Où | Quand |
|-------|------|----|-------|
| 1 | Working paper FR + EN, 12 à 20 pages, avec le catalogue d'indétermination et la suite de cas-tests | HAL (portail Mines Paris-PSL) et arXiv (math.OC ou econ.GN) ; code sur GitHub avec DOI Zenodo | mi-novembre 2026 |
| 2 | Post LinkedIn et page web, relayés par SENELEC, EPEX, Mines | site du projet | même semaine, puis rappel au lancement du DAM (1er janvier 2027) |
| 3 | Article de conférence 6 pages (format IEEE) | IEEE PES/IAS PowerAfrica 2027 (dates non annoncées) ; EEM 2027 à TU Dresden (eem27.de, appel à communications non encore publié, échéance habituellement en début d'année) | soumission T1 2027 |
| 4 | Article de revue si les retours du WAPP le justifient | Utilities Policy, The Electricity Journal, Energy for Sustainable Development | 2027 |

Titre de travail : « An open reference implementation of day-ahead zonal market coupling for the West African Power Pool: formulation, order types and indeterminacy rules ».

Auteurs : Kodjovi Plakoo, Enrico Patane, El Hadji Tamsir Diop, Adrien Atayi, encadrant Mines à confirmer.

Faits publics à citer correctement dans le papier :
- ICC du WAPP inauguré le 17 novembre 2023 à Abomey-Calavi, équipé SCADA, EMS et MMS.
- GE Vernova : GridOS, EMS, WAMS et Advanced Market Management System dans l'ICC (communiqué d'octobre 2024).
- Tarifs du DAM validés par les régulateurs fin 2025, premier essai de synchronisation sur douze pays (Banque mondiale, mai 2026).
- Opérateurs en formation sur le système de trading en vue du lancement.

---

## 5. Produit : site et application

Séparer trois objets, livrables indépendamment :

1. **Site vitrine** (statique, bilingue, design moderne) : présentation, lien vers le papier, les cas-tests, GitHub et l'application. Une semaine de travail. Peut sortir en même temps que le working paper.
2. **Moteur en paquet Python** avec ligne de commande et API REST (FastAPI) : `pip install`, fichiers CSV ou JSON en entrée (zones, lignes et NTC, ordres), résultats en sortie. C'est ce qui rend « le module opérationnel » pour un tiers, indépendamment de toute interface. Deux semaines.
3. **Application web** : nouveau front en React (Next.js, Tailwind, graphiques Plotly.js ou ECharts) consommant l'API ; salles de session par code, rôles formateur et trader, bilingue, vue « mon résultat ». Quatre à six semaines. Sortir de Streamlit est justifié pour le design, le multi-session et la pérennité, mais **ne doit pas retarder la publication**. Solution de repli : garder Streamlit corrigé et restylé derrière le site vitrine jusqu'au nouveau front.

Architecture cible :

```
GitHub (Apache-2.0)
├── wapp_clearing/      moteur Pyomo, règles de prix, cas-tests, CLI      → PyPI
├── api/                FastAPI : /clear, /scenarios, /rooms              → Docker
├── web/                Next.js : site vitrine + application              → Docker ou Vercel
└── docs/               working paper, formulation, guide utilisateur    → site
```

---

## 6. Hébergement et nom de domaine

**Recommandation : acheter un nom de domaine propre** (10 à 15 € par an, en `.org`), pour trois raisons : indépendance vis-à-vis de la DSI de Mines Paris (projet externe, validations lentes, règles d'hébergement), pérennité après la fin de la scolarité, neutralité entre les trois partenaires (Mines, SENELEC, EPEX) dont les logos et affiliations figurent sur le site. Le dépôt HAL apporte le label académique sans dépendre du domaine. Une redirection depuis un sous-domaine Mines peut s'ajouter plus tard si l'école le propose.

Hébergement : un petit VPS (OVH ou Hetzner, 5 à 10 € par mois) avec Docker Compose et Caddy pour le HTTPS. Données sous notre contrôle, plusieurs formations en parallèle. Pour la démo publique seule, Vercel (front) et Fly.io ou Render (API) suffisent en offre gratuite. Streamlit Community Cloud reste utile pour une démo immédiate.

Points juridiques : licence Apache-2.0 (clause brevets) ou MIT ; avertissement sur les NTC estimées et les profils types ; pas de logo WAPP sans accord ; aucune donnée personnelle au-delà d'un nom d'affichage.

---

## 7. Calendrier proposé

| Semaine | Travail |
|---------|---------|
| 6 au 10 octobre | Décisions : nom, domaine, licence, auteurs. Dépôt GitHub privé. Lot 0 de correctifs. Plan détaillé du working paper. |
| 13 octobre au 31 octobre | Moteur v2 : prix dans l'ensemble dual, départage exact, MILP blocs, liés, exclusifs, blocs paradoxaux. Suite de cas-tests. Paquet Python, CLI, API. |
| 3 au 14 novembre | Rédaction du working paper FR et EN, relecture Tamsir et Adrien. Site vitrine. Dépôt HAL, arXiv, Zenodo. GitHub public. Post LinkedIn n°1. |
| 17 novembre au 31 décembre | Nouveau front React, hébergement, formation pilote interne SENELEC, retours. |
| 1er janvier 2027 | Post LinkedIn n°2 au lancement du DAM, application en ligne. |
| T1 2027 | Soumission conférence (PowerAfrica ou EEM). Formation WAPP ou ERERA sur demande. |

---

## 8. Rôles

- **Kodjovi** : moteur, API, front, déploiement, rédaction technique.
- **Enrico** : à confirmer (co-auteur, cas-tests, relecture).
- **Tamsir** : contexte WAPP et SENELEC, accès aux données réelles, validation des règles de marché, diffusion vers WAPP et ERERA, sondage sur le nom et le logo.
- **Adrien** : validation des règles de prix et de départage par rapport à EUPHEMIA, blocs paradoxaux, MIC, relecture, canal EPEX et EEM.
- **Mines Paris-PSL** : affiliation, dépôt HAL, encadrant signataire.

---

## 9. Décisions à prendre cette semaine

1. Nom du produit et nom de domaine (et qui l'achète).
2. Licence du code.
3. Liste des auteurs et ordre.
4. Streamlit restylé en attendant, ou attendre le front React pour mettre l'application en ligne.
5. Date cible du working paper (proposition : 14 novembre 2026).
