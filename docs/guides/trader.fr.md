# Guide du trader

Vous représentez une organisation d'un pays du West African Power Pool sur le marché du lendemain. Vous déposez des offres de vente et d'achat pour chaque heure, le formateur lance le clearing, et vous découvrez ce qui a été accepté, à quel prix, et ce que vous avez gagné.

## 1. Entrer dans la salle

Depuis l'accueil, saisissez le code donné par le formateur, votre organisation et votre zone. Le nom doit être unique dans la salle. Si vous choisissez un nom proposé dans la liste, vous prenez la place de l'acteur réel correspondant dans les données de fond (ses centrales ou sa demande disparaissent, les vôtres les remplacent). Avec un nom libre, vos ordres s'ajoutent au marché existant.

## 2. Déposer ses ordres

Le carnet d'ordres a quatre onglets. « Enregistrer » remplace l'ensemble de vos ordres par ce qui est à l'écran ; vous pouvez modifier jusqu'à la clôture de la soumission.

**Vente.** Une ligne par segment : nom de la centrale, numéro de segment (0 à 3, prix croissants pour un même actif), quantité en MW, prix en monnaie par MWh, profil horaire. Le profil module la quantité disponible heure par heure : *baseload* 95 % toute la journée, *hydro* entre 60 et 100 % selon l'heure, *solar* nul la nuit et maximal à midi, *peaker* et *flat* 100 %. Un segment peut être accepté partiellement.

**Achat.** Même logique : nom de la charge, quantité à la pointe, prix maximal que vous acceptez de payer. La quantité suit automatiquement le profil de charge ouest-africain (creux la nuit, pointe le soir).

**Blocs.** Un bloc est accepté en totalité sur toutes ses heures, ou rejeté : utile pour une centrale qui ne peut pas démarrer pour deux heures, ou une consommation industrielle continue. Un bloc *enfant* n'est accepté que si son *parent* l'est (indiquez le nom du parent). Dans un *groupe exclusif* (même étiquette de groupe), une seule option au plus est retenue.

**MIC.** Condition de revenu minimum pour un vendeur : si votre recette aux prix finals est inférieure au terme fixe plus le terme variable multiplié par le volume accepté, toutes vos offres sont retirées et le marché est recalculé sans vous.

## 3. Comprendre le résultat

- Chaque pays reçoit un **prix par heure**. Une offre de vente est acceptée si son prix est inférieur ou égal au prix de sa zone, une offre d'achat si son prix est supérieur ou égal. L'offre dont le prix est exactement celui de la zone peut n'être acceptée qu'en partie.
- Sans congestion, deux pays reliés ont le **même prix**. Quand une ligne est saturée, le pays importateur est plus cher : c'est visible sur la carte, ligne en rouge.
- Un **bloc** peut être rejeté alors qu'il aurait été gagnant aux prix finals : l'accepter aurait changé les prix de tout le monde et réduit la valeur totale. C'est un rejet paradoxal, normal dans ce type de marché. Un bloc n'est jamais accepté à perte.
- Vous êtes payé ou vous payez au **prix de votre zone**, pas à votre prix d'offre : votre surplus est la différence.

## 4. Lire « Mon résultat »

Vendu et acheté (accepté sur offert), surplus, nombre d'ordres rejetés, détail par actif avec le prix moyen obtenu, statut de vos blocs, prix horaires de votre zone. Les résultats arrivent en direct dès que le formateur a lancé le clearing.

## 5. Conseils

- Offrez vos centrales à leur **coût variable** : au-dessus, vous risquez d'être rejeté ; au-dessous, vous risquez de vendre à perte.
- Découpez une centrale en segments de prix croissants plutôt qu'un seul bloc de prix.
- Utilisez un bloc seulement si la contrainte « tout ou rien » est réelle : il peut vous faire perdre une vente qu'un segment aurait obtenue.
- Regardez les lignes saturées : un pays isolé par la congestion fixe son propre prix.
