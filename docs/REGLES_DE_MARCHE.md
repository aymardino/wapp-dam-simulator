# Règles de marché appliquées par le moteur

*Document de référence pour la note technique et pour toute comparaison avec une autre plateforme de clearing. Chaque règle ci-dessous est implémentée dans `engine/clearing.py` et vérifiée par `tests/test_engine.py`. Version du 2 octobre 2026.*

**Summary (English).** This document states every rule the clearing engine applies: inputs, order types, the three sequential problems (welfare maximisation, volume tie-break, pricing), the complete characterisation of admissible prices, the treatment of paradoxical blocks, tolerances, and what is deliberately not modelled. It is the counterpart of the formulation in Livrable 2 and is meant to be testable: the public test cases in `tests/` give expected outcomes for each rule.

---

## 1. Périmètre

- 14 zones de marché (pays du WAPP), 15 interconnexions, approche zonale par capacités de transfert nettes (NTC), sans flow-based.
- Horizon : la journée J+1, 24 pas horaires, ou tout sous-ensemble d'heures (mode 1 h pour la formation).
- Une offre vaut pour toutes les heures simulées ; la quantité effective d'une heure est la quantité soumise multipliée par le profil horaire (production) ou par le profil de charge ouest-africain (demande), arrondie au MW.
- Prix bornés : 0 et 500 par MWh (monnaie paramétrable, sans effet sur le calcul).
- Contrainte d'interdépendance : flux GHA→BFA + flux CIV→BFA ≤ α × (NTC GHA-BFA + NTC CIV-BFA), α = 0,7.

## 2. Types d'ordres

| Type | Variable | Acceptation | Effet sur le prix |
|------|----------|-------------|-------------------|
| Segment de vente ou d'achat (stepwise, 4 segments par acteur au plus) | x ∈ [0, 1] | partielle possible | peut être marginal (fixe le prix) |
| Bloc simple (fill-or-kill) | y ∈ {0, 1} | totale sur toutes ses heures ou nulle | ne fixe jamais le prix |
| Bloc lié | y_enfant ≤ y_parent | l'enfant exige le parent | idem |
| Groupe exclusif | Σ y ≤ 1 | au plus une option | idem |

Le parent d'un bloc et son groupe exclusif sont identifiés par nom au sein du même trader et de la même zone.

## 3. Les trois problèmes, dans l'ordre

### P1 — Qui échange ? (welfare)

Maximiser la valeur créée : somme sur les heures de (prix des achats acceptés × quantités) moins (prix des ventes acceptées × quantités), blocs compris, sous l'équilibre de chaque zone à chaque heure (production + importations nettes = consommation), les bornes de flux, la contrainte α et les contraintes de liaison des blocs. Programme linéaire sans bloc, programme linéaire en nombres entiers avec blocs (gap relatif 10⁻⁶).

### P1bis — Comment départager ? (volume)

Parmi les solutions de welfare optimal, maximiser le volume accepté (ventes + achats). Les décisions de blocs sont fixées à celles de P1. **Le welfare est contraint à sa valeur optimale exacte** (W ≥ W*), et non à W* − 0,01 comme dans le Livrable 2 : une tolérance absolue était intégralement consommée par la maximisation du volume et produisait une solution que plus aucun prix ne supportait. Si le solveur ne trouve pas de solution (cas numérique), la solution de P1 est conservée et le diagnostic `tie_break` l'indique.

Ce départage ne tranche pas tous les ex æquo : deux offres au même prix dans la même zone peuvent encore être partagées de plusieurs façons sans changer ni le welfare ni le volume. Une **règle de partage explicite** est donc appliquée ensuite, par groupe (zone, heure, sens, prix) partiellement accepté : `prorata` (défaut, chaque offre du groupe est acceptée dans la même proportion de sa quantité), `order` (ordre de soumission, premier servi) ou `solver` (répartition laissée au solveur). Le total accepté du groupe est inchangé : ni le welfare, ni le volume, ni l'ensemble des prix admissibles ne bougent.

### P2 — À quel prix ? (prix zonaux)

**Ensemble des prix admissibles** (conditions de Karush-Kuhn-Tucker de P1, à décisions de blocs fixées), pour chaque zone z et chaque heure h :

1. vente acceptée en totalité ⇒ π ≥ prix de l'offre ;
2. vente partiellement acceptée ⇒ π = prix de l'offre ;
3. vente rejetée ⇒ π ≤ prix de l'offre ;
4. achat accepté en totalité ⇒ π ≤ prix de l'offre ;
5. achat partiellement accepté ⇒ π = prix de l'offre ;
6. achat rejeté ⇒ π ≥ prix de l'offre ;
7. ligne u→v non saturée ⇒ π_v = π_u ;
8. ligne saturée dans le sens u→v ⇒ π_v ≥ π_u, et inversement ;
9. si la contrainte α est active, les deux lignes vers BFA partagent un même supplément de prix λ ≥ 0 ;
10. bornes réglementaires 0 ≤ π ≤ 500.

Les règles 3, 6, 7 et 9 sont les ajouts de la v2 par rapport aux contraintes (8)-(12) du Livrable 2 ; sans elles, le moteur produisait des ordres simples paradoxalement rejetés et des écarts de prix entre zones non congestionnées.

**Sélection dans l'ensemble admissible** : le prix retenu minimise la somme des écarts absolus au prix de référence, où le prix de référence est le milieu de l'intervalle admissible local [borne basse, borne haute], avec borne basse = max(prix des ventes acceptées, prix des achats rejetés, 0) et borne haute = min(prix des achats acceptés, prix des ventes rejetées, 500). Quand le prix est unique (cas général), la règle n'a aucun effet ; elle ne tranche que les cas d'indétermination, et dans une zone sans échange elle place le prix à mi-chemin entre la meilleure demande et la meilleure offre rejetées.

Le mode `pricing = 'l2'` reproduit exactement la règle du Livrable 2 à des fins de comparaison.

## 4. Blocs paradoxaux

Après P2, le surplus de chaque bloc est calculé aux prix finals : Σ_h (π_h − p) × q pour une vente, Σ_h (p − π_h) × q pour un achat.

- **PAB** (bloc accepté à perte, surplus < 0) : interdit. Règle `euphemia` (défaut) : le bloc est fixé à « rejeté » et la séquence P1 → P1bis → P2 est relancée, jusqu'à absence de PAB (au plus un bloc fixé par itération, donc au plus autant d'itérations que de blocs ; plafond paramétrable).
- **PRB** (bloc rejeté qui aurait un surplus > 0) : toléré et signalé, comme dans EUPHEMIA. Le rejeter était optimal pour le welfare total : l'accepter aurait déplacé les prix.
- Règle `l2` : en plus, les PRB sont fixés à « accepté » (texte du Livrable 2 §3.3). Règle `none` : détection seule.

## 5. Minimum Income Condition (MIC)

Un acteur vendeur peut assortir ses offres d'une condition de revenu minimum : terme fixe F et terme variable V par MWh. Après P2, sa recette aux prix finals (segments et blocs portant son nom) est comparée à F + V × volume accepté. Si elle est inférieure (à MIC_TOL près) et que du volume lui a été accepté, **toutes ses offres sont retirées** (ses blocs, et les blocs enfants qui en dépendent) et la séquence P1 → P1bis → P2, boucle PAB comprise, est relancée sans lui. Un acteur dont rien n'est accepté satisfait trivialement sa condition. La boucle s'arrête quand toutes les conditions restantes sont satisfaites ; au plus une itération par condition. Les prix publiés sont ceux de la dernière exécution. La formulation « revenu − coût ≥ F » du Livrable 2 §6.3 s'obtient en posant V égal au coût variable de l'acteur.

## 6. Tolérances

| Grandeur | Valeur | Rôle |
|----------|--------|------|
| X_TOL | 10⁻⁴ | un ratio x < X_TOL est « rejeté », x > 1 − X_TOL « accepté en totalité », entre les deux « partiel » |
| F_TOL | 10⁻³ MW | une ligne est saturée si le flux est à moins de F_TOL de sa borne |
| PRICE_TOL | 0,5 par MWh | tolérance des diagnostics (ordres paradoxaux, écarts de prix) |
| MIC_TOL | 0,5 (monnaie) | tolérance de la condition de revenu minimum |
| gap MILP | 10⁻⁶ relatif | optimalité des problèmes avec blocs |
| arrondi des quantités horaires | 1 MW | quantité effective = round(q × profil) |

## 7. Sorties et vérifications

Pour chaque clearing, le moteur publie : prix par zone et par heure, flux signés par ligne, dispatch par profil, résultats par acteur (volume offert et accepté, prix moyen, recette ou paiement, surplus, offres rejetées), décomposition par zone (surplus consommateur, surplus producteur, position nette, heures sans échange), rente de congestion et heures saturées par ligne, statut de chaque bloc, état de chaque condition MIC (recette, revenu requis, satisfaite ou retirée), et des **diagnostics** : nombre d'ordres simples paradoxalement rejetés ou acceptés (attendu : 0), nombre de lignes non saturées à prix différents (attendu : 0), écart maximal aux conditions d'équilibre, mode de départage, itérations PAB, et l'identité welfare = surplus consommateur + surplus producteur + rente de congestion.

## 8. Ce qui n'est pas modélisé

Pertes, réserves, rampes, durées minimales de fonctionnement, enchères intrajournalières, règlement financier, flow-based, courbes d'offre interpolées (les segments sont des marches), arrondi final des prix publiés, MIC côté achat.
