/* All the text of the video, in French and English: the one file to edit for a wording change or a translation.
   Read through WAPP.t("key") (assets/wapp.js), which also applies French typography (non-breaking spaces before
   : ; ? ! and inside « »). {placeholders} are filled by WAPP.t("key", { name: value }).
   Keep every line short: this is motion-graphics copy, read in a few seconds, not narration. */
window.WAPP_STRINGS = {
  fr: {
    badge: 'Simulation · données 2024 reconstituées',
    hour: '{h} h',                         // 19 h

    // 01 · intro: the logo assembles
    's01.kicker': 'Simulateur ouvert',
    's01.wordmark': 'WAPP DAM Simulator',
    's01.tagline': 'Le marché de l’électricité d’Afrique de l’Ouest, à livre ouvert',

    // 02 · the region
    's02.kicker': 'Afrique de l’Ouest',
    's02.countries': 'pays',
    's02.lines': 'lignes d’interconnexion',
    's02.title': 'Un marché commun de l’électricité, prévu pour 2027',

    // 03 · the question
    's03.line1': 'Chaque jour,',
    's03.line2': 'pour chacune des 24 heures du lendemain :',
    's03.q1': 'Qui vend ?',
    's03.q2': 'Qui achète ?',
    's03.q3': 'À quel prix ?',

    // 04 · supply meets demand (data: WAPP.data.cross)
    's04.kicker': '{zone}, {hour}',
    's04.supply': 'Les centrales, de la moins chère à la plus chère',
    's04.demand': 'Les acheteurs, du plus offrant au moins offrant',
    's04.meet': 'Le prix se fixe à leur rencontre',
    's04.price': '{p} $/MWh',
    's04.marginal': 'fixé par la dernière centrale appelée',
    's04.axisQ': 'MW',
    's04.axisP': '$/MWh',

    // 05 · a line fills up (data: WAPP.data.congestion)
    's05.kicker': 'Les lignes entre pays',
    's05.free': 'La ligne a de la place : un seul prix',
    's05.full': 'La ligne est pleine : les prix se séparent',
    's05.capacity': 'capacité',
    's05.flow': '{f} / {cap} MW',

    // 06 · the engine
    's06.kicker': 'Le calcul',
    's06.title': 'Trois questions, dans l’ordre',
    's06.q1': 'Qui est servi ?',
    's06.a1': 'Les échanges qui créent le plus de valeur',
    's06.q2': 'Combien ?',
    's06.a2': 'À valeur égale, le plus d’énergie',
    's06.q3': 'À quel prix ?',
    's06.a3': 'Le prix du milieu, parmi tous ceux possibles',
    's06.low': 'plus bas possible',
    's06.mid': 'retenu',
    's06.high': 'plus haut possible',
    's06.foot': 'Optimisation mathématique · solveur libre HiGHS',

    // 06a · question 1 in detail: the value created, under constraints (data: WAPP.data.cross)
    's6a.kicker': '1 · Qui est servi ?',
    's6a.title': 'Le plus de valeur créée',
    's6a.buyers': 'Les acheteurs gagnent ce qu’ils étaient prêts à payer, moins le prix',
    's6a.sellers': 'Les vendeurs gagnent le prix, moins ce qu’ils demandaient',
    's6a.sum': 'Le moteur rend la somme la plus grande possible, sur les 14 pays et les 24 heures',
    's6a.under': 'Sous trois contraintes',
    's6a.c1': 'Chaque pays équilibré, heure par heure',
    's6a.c2': 'Des flux sous la capacité des lignes',
    's6a.c3': 'Des blocs acceptés en entier, ou pas du tout',

    // 06b · question 3 in detail: when several prices fit, the middle one (data: WAPP.data.midpoint)
    's6b.kicker': '3 · À quel prix ?',
    's6b.title': 'Quand plusieurs prix conviennent, le milieu',
    's6b.case': '{zone}, {hour} : la ligne qui vient du Nigeria est pleine',
    's6b.hiLab': 'Centrale à {p} $ : non appelée',
    's6b.hiWhy': 'au-dessus, elle voudrait produire',
    's6b.loLab': 'Acheteurs à {p} $ : non servis',
    's6b.loWhy': 'en dessous, ils voudraient acheter',
    's6b.band': 'tous ces prix respectent les échanges',
    's6b.pick': '{p} $/MWh : le milieu',
    's6b.rule': 'Le moteur publie le milieu de l’intervalle',

    // 06c · special case: an all-or-nothing block accepted at a loss (an illustration, not data)
    's6c.kicker': 'Cas particulier',
    's6c.title': 'Une offre « tout ou rien » acceptée à perte est retirée',
    's6c.badge': 'Illustration',
    's6c.block': 'Bloc · 100 MW · 4 h · {p} $/MWh',
    's6c.loss': 'Prix moyen {m} $ : en dessous de son prix',
    's6c.out': 'Retiré',
    's6c.again': 'On recalcule',
    's6c.stable': 'Plus aucun bloc à perte : le résultat est publié',
    's6c.mic': 'Même règle pour un revenu minimum non atteint',

    // 07 · a whole day (data: WAPP.data.day, prices, flows)
    's07.kicker': 'Une journée simulée',
    's07.title': '14 pays, 24 heures, un prix par heure',
    's07.welfare': 'valeur créée',
    's07.volume': 'énergie échangée',
    's07.saturated': 'lignes pleines au moins une heure',
    's07.flow': 'flux',
    's07.full': 'ligne pleine',

    // 08 · uses
    's08.title': 'Pour former, étudier, comparer',
    's08.k1': 'Former',
    's08.v1': 'Une séance en trois manches, chacun dans le rôle d’un acteur',
    's08.k2': 'Étudier',
    's08.v2': 'Des règles écrites, un moteur ouvert',
    's08.k3': 'Comparer',
    's08.v3': 'Rejouer un cas avant le lancement du marché',
    's08.credit': 'Photo : IAfrica76, CC0',

    // 09 · outro
    's09.wordmark': 'WAPP DAM Simulator',
    's09.url': 'wapp-dam-simulator.mastereose.fr',
    's09.open': 'Code ouvert · Apache 2.0',
    's09.authors': 'Kodjovi Plakoo · Enrico Patanè',
    's09.frame': 'Mastère Spécialisé OSE, Mines Paris – PSL, avec SENELEC',
    's09.disclaimer': 'Outil pédagogique indépendant, non affilié au WAPP. Prix simulés sur des données 2024 reconstituées.',
  },
  en: {
    badge: 'Simulation · reconstructed 2024 data',
    hour: '{hh}:00',                       // 19:00

    's01.kicker': 'Open simulator',
    's01.wordmark': 'WAPP DAM Simulator',
    's01.tagline': 'The West African electricity market, computed in the open',

    's02.kicker': 'West Africa',
    's02.countries': 'countries',
    's02.lines': 'interconnection lines',
    's02.title': 'A common electricity market, planned for 2027',

    's03.line1': 'Every day,',
    's03.line2': 'for each of the next day’s 24 hours:',
    's03.q1': 'Who sells?',
    's03.q2': 'Who buys?',
    's03.q3': 'At what price?',

    's04.kicker': '{zone}, {hour}',
    's04.supply': 'Power plants, from cheapest to most expensive',
    's04.demand': 'Buyers, from highest bid to lowest',
    's04.meet': 'The price is set where they meet',
    's04.price': '{p} $/MWh',
    's04.marginal': 'set by the last plant called',
    's04.axisQ': 'MW',
    's04.axisP': '$/MWh',

    's05.kicker': 'The lines between countries',
    's05.free': 'The line has room: one single price',
    's05.full': 'The line is full: prices split',
    's05.capacity': 'capacity',
    's05.flow': '{f} / {cap} MW',

    's06.kicker': 'The computation',
    's06.title': 'Three questions, in order',
    's06.q1': 'Who is served?',
    's06.a1': 'The trades that create the most value',
    's06.q2': 'How much?',
    's06.a2': 'At equal value, the most energy',
    's06.q3': 'At what price?',
    's06.a3': 'The middle price, among all possible ones',
    's06.low': 'lowest possible',
    's06.mid': 'chosen',
    's06.high': 'highest possible',
    's06.foot': 'Mathematical optimisation · open-source HiGHS solver',

    's6a.kicker': '1 · Who is served?',
    's6a.title': 'The most value created',
    's6a.buyers': 'Buyers gain what they were ready to pay, minus the price',
    's6a.sellers': 'Sellers gain the price, minus what they asked',
    's6a.sum': 'The engine makes the sum as large as possible, over the 14 countries and the 24 hours',
    's6a.under': 'Under three constraints',
    's6a.c1': 'Each country balanced, hour by hour',
    's6a.c2': 'Flows within the capacity of the lines',
    's6a.c3': 'Blocks accepted in full, or not at all',

    's6b.kicker': '3 · At what price?',
    's6b.title': 'When several prices fit, the middle one',
    's6b.case': '{zone}, {hour}: the line from Nigeria is full',
    's6b.hiLab': 'Plant at {p} $: not called',
    's6b.hiWhy': 'above, it would want to produce',
    's6b.loLab': 'Buyers at {p} $: not served',
    's6b.loWhy': 'below, they would want to buy',
    's6b.band': 'every price here respects the trades',
    's6b.pick': '{p} $/MWh: the middle',
    's6b.rule': 'The engine publishes the middle of the interval',

    's6c.kicker': 'Special case',
    's6c.title': 'An “all or nothing” order accepted at a loss is withdrawn',
    's6c.badge': 'Illustration',
    's6c.block': 'Block · 100 MW · 4 h · {p} $/MWh',
    's6c.loss': 'Average price {m} $: below its price',
    's6c.out': 'Withdrawn',
    's6c.again': 'Compute again',
    's6c.stable': 'No block at a loss any more: the result is published',
    's6c.mic': 'Same rule for a minimum income not reached',

    's07.kicker': 'A simulated day',
    's07.title': '14 countries, 24 hours, one price per hour',
    's07.welfare': 'value created',
    's07.volume': 'energy traded',
    's07.saturated': 'lines full at least one hour',
    's07.flow': 'flow',
    's07.full': 'full line',

    's08.title': 'To train, study, compare',
    's08.k1': 'Train',
    's08.v1': 'A three-round session, everyone plays an actor',
    's08.k2': 'Study',
    's08.v2': 'Written rules, an open engine',
    's08.k3': 'Compare',
    's08.v3': 'Replay a case before the market opens',
    's08.credit': 'Photo: IAfrica76, CC0',

    's09.wordmark': 'WAPP DAM Simulator',
    's09.url': 'wapp-dam-simulator.mastereose.fr',
    's09.open': 'Open code · Apache 2.0',
    's09.authors': 'Kodjovi Plakoo · Enrico Patanè',
    's09.frame': 'Advanced Master OSE, Mines Paris – PSL, with SENELEC',
    's09.disclaimer': 'Independent educational tool, not affiliated with the WAPP. Prices simulated on reconstructed 2024 data.',
  },
}
