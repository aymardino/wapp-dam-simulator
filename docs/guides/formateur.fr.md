# Guide du formateur

Ce guide décrit le déroulement d'une séance de formation avec le simulateur et la signification de chaque réglage. Le poste du formateur s'ouvre en créant une salle depuis l'accueil ; le code à six caractères affiché dans le bandeau est à partager aux participants.

## 1. Préparer la séance

1. **Créer la salle** depuis l'accueil (nom de la formation, votre nom). Le navigateur qui crée la salle devient le poste du formateur : ne le prêtez pas pendant la séance.
2. **Choisir l'horizon** : 24 heures pour une journée complète, ou une seule heure (par exemple 19 h, la pointe) pour une manche rapide.
3. **Choisir le scénario** : il fournit les données de fond (centrales, demandes, capacités des lignes). Il n'y a qu'un jeu de base, « Référence 2024 (sources publiques) » ; les quatre variantes (« Sécheresse hydraulique », « Ligne Nigeria–Bénin indisponible », « Gaz cher », « Forte demande ») ne changent qu'une chose et servent aux manches suivantes, pour montrer l'effet d'un seul choc.
4. **Choisir le mode de complétion**, qui décide de ce qui se passe pour les acteurs que personne n'incarne (voir §4).
5. **Vérifier les capacités des lignes (NTC)** si vous voulez provoquer ou lever une congestion.
6. **Partager le code** et faire entrer les participants.

## 2. Déroulé type (deux heures)

| Temps | Manche | Objectif pédagogique |
|------:|--------|----------------------|
| 0:00 | Entrée des participants, présentation de la carte et des règles | vocabulaire : offre, demande, prix de zone, NTC |
| 0:15 | Manche 1 : offres par segments, scénario de référence, 24 h | ordre de mérite, prix uniforme, acceptation partielle |
| 0:45 | Manche 2 : mêmes acteurs, ajout de blocs tout ou rien | blocs acceptés ou rejetés en totalité, rejets paradoxaux |
| 1:15 | Manche 3 : scénario « Sécheresse hydraulique » ou « Ligne Nigeria–Bénin indisponible » | congestion, divergence des prix, rente de congestion |
| 1:45 | Débrief sur la page Résultats et les résultats individuels | lecture des vérifications, discussion des stratégies |

Entre deux manches : « Rouvrir la soumission », changer le scénario ou les NTC, et demander aux participants de revoir leurs ordres. Chaque clearing est conservé dans l'historique.

## 3. Pendant la manche

- Le panneau **Participants** montre qui est entré et combien d'ordres chacun a déposés. Le bandeau indique « En direct » : tout se met à jour sans recharger.
- **Clôturer la soumission** quand tout le monde a déposé, puis **Lancer le clearing**. Le calcul prend moins d'une seconde ; avec de nombreux blocs, quelques secondes.
- Le panneau **Résultats** s'ouvre sur la carte (prix par pays à l'heure choisie, flux par ligne, lignes saturées en rouge), puis les onglets Prix, Dispatch et Flux, et le tableau par zone.
- Les badges verts en tête des résultats sont les **vérifications** : aucun ordre paradoxalement rejeté, aucun écart de prix sans congestion, départage exact. Un badge orange signale un bloc paradoxalement rejeté (toléré) ou une condition de revenu minimum qui a retiré un acteur.
- **Retirer un participant** (nom inapproprié, doublon) est possible depuis l'API ; ses ordres sont supprimés.

## 4. Les réglages expliqués

**Mode de complétion.** Les participants n'incarnent jamais tous les acteurs des quatorze pays. Trois comportements possibles :
- *Acteurs de fond* (recommandé) : tous les acteurs du scénario restent dans le marché, sauf ceux qu'un participant remplace. Un participant remplace les acteurs de **sa zone** dont le nom correspond au sien (« SENELEC » remplace « SENELEC Thermal » et « SENELEC Demand », « CEB » remplace « CEB Nangbeto ») ou au nom d'un de ses ordres (un ordre nommé « Egbin Gas » remplace la centrale de référence Egbin Gas). Un participant au nom libre, par exemple « Équipe 1 », ne remplace rien : ses ordres s'ajoutent au marché. Choisissez le nom dans la liste proposée pour prendre la place d'un acteur réel.
- *Zones sans soumission* : une zone où au moins un participant a déposé un ordre ne contient **que** les ordres des participants ; les autres zones sont complétées par le scénario. Utile pour qu'un pays soit entièrement joué par ses traders.
- *Aucune* : seuls les ordres des participants comptent. Le clearing est refusé s'il n'y en a aucun.

**Règle de prix.** *P2 complet* (recommandé) choisit, parmi tous les prix compatibles avec les quantités acceptées (ordres acceptés, rejetés, lignes saturées ou non), le prix le plus proche du milieu de l'intervalle. *P2 du Livrable 2* reproduit la règle initiale du projet, qui ignorait les ordres rejetés et l'égalité des prix sur les lignes non saturées ; à utiliser seulement pour montrer la différence.

**Blocs paradoxaux.** *EUPHEMIA* (recommandé) rejette itérativement les blocs acceptés à perte et tolère les blocs rejetés qui auraient été gagnants. *Livrable 2* force en plus l'acceptation de ces derniers quand c'est possible. *Détection seule* n'applique aucune correction.

**Partage des ex æquo.** Quand plusieurs offres au même prix ne peuvent pas toutes être servies : *prorata* des quantités (recommandé), *ordre de soumission*, ou *laissé au solveur*.

**Monnaie.** Simple libellé d'affichage, sans effet sur le calcul.

**Capacités (NTC).** Valeurs du scénario, modifiables ligne par ligne ; « Réinitialiser » revient aux valeurs du scénario.

## 5. Lire les résultats

- **Welfare** : valeur créée par les échanges, somme du surplus des acheteurs, du surplus des vendeurs et de la rente de congestion.
- **Volume** : énergie échangée sur la période.
- **Prix par zone** : un pays importateur dont les lignes sont saturées a un prix supérieur à ses voisins ; sans congestion les prix sont égaux.
- **Position nette** : positive pour un exportateur, négative pour un importateur.
- **Surplus par zone** : ce que les acteurs du pays gagnent par rapport à leurs prix d'offre.
- **Exports** : prix en CSV, résultat complet en JSON, pour un débrief sur tableur.

## 6. Questions fréquentes

- *Le welfare vaut 45 millions alors que personne n'a déposé d'ordre.* C'est le mode de complétion : le marché a tourné sur les données du scénario. Le bandeau « Démonstration » le signale.
- *Un trader ne peut plus modifier ses ordres.* La soumission est clôturée ; rouvrez-la.
- *Je veux tester comme trader depuis mon poste.* Utilisez le lien « Entrer dans la salle comme trader » ; vos deux identités restent accessibles depuis l'accueil.
- *Le calcul est refusé.* Le message indique la cause : ordre hors bornes, aucun ordre avec complétion désactivée.
