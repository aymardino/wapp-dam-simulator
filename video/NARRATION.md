# Voice-over of the video

The video works without sound (all the text is on screen); this is the narration that can go with it, scene by scene,
in French and in English. It completes the screen rather than reading it. Each line fits its scene at a calm pace
(about 2.5 words per second); the "max" column is the time available.

## How to record

- A quiet room with soft furnishings (a bedroom is better than a kitchen), the phone or microphone about 30 cm away,
  the same place and the same distance for every take.
- One file per scene, named after the scene: `01-intro.wav`, `02-region.wav`, … (WAV or M4A; a voice memo app is
  fine). Half a second of silence before and after.
- A natural, calm voice, as if explaining to a colleague; numbers as written ("cent cinquante-cinq dollars").
- Re-record a scene rather than cutting inside it. If a take is longer than its "max", say so: the scene is lengthened.
- Put the files in `video/assets/voice/fr/` and `video/assets/voice/en/`, then `npm run render`: the voice is mixed
  in at the start of each scene and its loudness evened out.

## Français

| Scène | Max | Texte |
| --- | --- | --- |
| 01-intro | 5 s | Le WAPP DAM Simulator : le marché ouest-africain de l’électricité, à livre ouvert. |
| 02-region | 8 s | Quatorze pays, reliés par quinze lignes, vont partager un même marché de l’électricité. Il doit ouvrir en 2027. |
| 03-question | 6 s | Chaque jour, pour chaque heure du lendemain : qui vend, qui achète, à quel prix ? |
| 04-curves | 11.5 s | Le Sénégal, à 19 heures. Les centrales se rangent de la moins chère à la plus chère ; les acheteurs, du plus offrant au moins offrant. Les courbes se croisent à cent cinquante-cinq dollars. |
| 05-network | 10.5 s | Entre le Nigeria et le Bénin, tant que la ligne a de la place, les deux pays paient le même prix. Quand elle est pleine, chacun garde le sien. |
| 06-engine | 10.5 s | Le moteur de calcul répond à trois questions, dans l’ordre fixé par les règles du marché : qui est servi, combien, et à quel prix. |
| 06a-value | 12 s | D’abord, qui est servi. Un échange crée de la valeur : ce que l’acheteur était prêt à payer, moins ce que le vendeur demandait. Le moteur maximise cette valeur, sans violer les contraintes. |
| 06b-price | 10 s | Ensuite, le prix. Au Niger à 16 heures, tout prix entre cent quatre-vingts et cent quatre-vingt-dix dollars respecte les échanges. Le moteur publie le milieu : cent quatre-vingt-cinq. |
| 06c-blocks | 9 s | Une offre tout ou rien acceptée à perte est retirée, et le calcul recommence, jusqu’à ce qu’aucune ne le soit plus. |
| 07-day | 9.5 s | Sur une journée entière, le simulateur calcule un prix par heure pour chacun des quatorze pays, et les flux sur chaque ligne. |
| 08-uses | 6.5 s | Il sert à former les équipes, à étudier les règles, et à comparer avant le lancement du marché. |
| 09-outro | 7 s | Le code est ouvert. Retrouvez le simulateur sur wapp-dam-simulator point mastereose point fr. |

## English

| Scene | Max | Text |
| --- | --- | --- |
| 01-intro | 5 s | The WAPP DAM Simulator: the West African electricity market, computed in the open. |
| 02-region | 8 s | Fourteen countries, linked by fifteen lines, are to share one electricity market. It is due to open in 2027. |
| 03-question | 6 s | Every day, for every hour of the next day: who sells, who buys, at what price? |
| 04-curves | 11.5 s | Senegal, seven in the evening. Power plants line up from cheapest to most expensive; buyers, from highest bid to lowest. The curves cross at one hundred and fifty-five dollars. |
| 05-network | 10.5 s | Between Nigeria and Benin, as long as the line has room, both countries pay the same price. When it is full, each keeps its own. |
| 06-engine | 10.5 s | The engine answers three questions, in the order the market rules set: who is served, how much, and at what price. |
| 06a-value | 12 s | First, who is served. A trade creates value: what the buyer was ready to pay, minus what the seller asked. The engine maximises that value, within the constraints. |
| 06b-price | 10 s | Then, the price. In Niger at four in the afternoon, any price between one hundred and eighty and one hundred and ninety dollars respects the trades. The engine publishes the middle: one hundred and eighty-five. |
| 06c-blocks | 9 s | An all-or-nothing order accepted at a loss is withdrawn, and the computation runs again, until none is left. |
| 07-day | 9.5 s | Over a whole day, the simulator computes one price per hour for each of the fourteen countries, and the flow on every line. |
| 08-uses | 6.5 s | It is for training teams, studying the rules, and comparing before the market opens. |
| 09-outro | 7 s | The code is open. Find the simulator at wapp-dam-simulator dot mastereose dot fr. |
