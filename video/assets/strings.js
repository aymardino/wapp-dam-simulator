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
