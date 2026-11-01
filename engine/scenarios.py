"""
Teaching scenarios: the Reference 2024 base set and its variants.
Each scenario returns (sell orders, buy orders, NTC) in the engine row format; it is used to fill zones
without submission and for the demonstration.
"""
from .clearing import default_rows, P_MAX, NTC


# ── "Reference 2024" set: available capacities and peak demands from public sources ──────────────────
# Details and sources: docs/REFERENCE_DATA.md. Values marked (est.) are estimates.
# Format: zone → ('S', name, [(MW, price USD/MWh), ...], profile) or ('D', name, [(MW, max price), ...])
REFERENCE_2024 = {
    'NGA': [
        ('S', 'Hydro Kainji-Jebba-Shiroro-Zungeru', [(800, 15), (700, 25)], 'hydro'),
        ('S', 'Egbin', [(500, 28), (400, 34)], 'baseload'),
        ('S', 'Azura-Edo CCGT', [(450, 24)], 'baseload'),
        ('S', 'Okpai CCGT', [(400, 26)], 'baseload'),
        ('S', 'NIPP et autres centrales gaz', [(800, 30), (800, 36), (600, 42), (300, 55)], 'baseload'),
        ('D', 'TCN Nigeria', [(3500, 230), (1500, 170), (800, 120)]),
    ],
    'GHA': [
        ('S', 'Hydro Akosombo-Kpong-Bui', [(700, 18), (500, 26), (300, 36)], 'hydro'),
        ('S', 'CCGT TICO-Cenpower-Amandi', [(900, 68), (500, 76)], 'baseload'),
        ('S', 'Sunon Asogli', [(400, 72), (150, 82)], 'baseload'),
        ('S', 'AKSA et autres OCGT', [(400, 95), (300, 115)], 'peaker'),
        ('S', 'Karpowership Ghana', [(300, 105), (170, 125)], 'peaker'),
        ('S', 'Solaire Ghana', [(120, 5)], 'solar'),
        ('D', 'ECG-NEDCo', [(2000, 220), (800, 160), (400, 110)]),
    ],
    'CIV': [
        ('S', 'Hydro CI-Energies (Soubré, Taabo, Kossou, Buyo)', [(500, 16), (400, 26)], 'hydro'),
        ('S', 'Azito CCGT', [(450, 48), (250, 58)], 'baseload'),
        ('S', 'CIPREL', [(350, 52), (200, 62)], 'baseload'),
        ('S', 'Atinkou CCGT', [(350, 46)], 'baseload'),
        ('S', 'Thermique HFO (Aggreko et autres)', [(60, 150), (40, 180)], 'peaker'),
        ('S', 'Solaire Côte d\'Ivoire', [(60, 5)], 'solar'),
        ('D', 'CIE Distribution', [(1400, 210), (500, 160), (300, 110)]),
    ],
    'SEN': [
        ('S', 'OMVS Manantali-Félou (part Sénégal)', [(80, 20)], 'hydro'),
        ('S', 'Solaire Sénégal', [(120, 4)], 'solar'),
        ('S', 'Éolien Taïba N\'Diaye', [(80, 8)], 'flat'),
        ('S', 'Charbon Sendou', [(110, 65)], 'baseload'),
        ('S', 'CCGT gaz (Cap des Biches, Malicounda)', [(300, 85), (200, 95)], 'baseload'),
        ('S', 'Thermique HFO (Kounoune, Tobène, Bel-Air)', [(250, 135), (200, 155), (100, 175)], 'peaker'),
        ('D', 'SENELEC Demand', [(800, 220), (300, 170), (150, 120)]),
    ],
    'BFA': [
        ('S', 'Solaire Burkina (Zagtouli, Nagréongo, Kodeni, Zina)', [(180, 5)], 'solar'),
        ('S', 'Hydro Bagré-Kompienga', [(25, 20)], 'hydro'),
        ('S', 'SONABEL thermique HFO', [(200, 160), (150, 185), (80, 210)], 'peaker'),
        ('D', 'SONABEL Demand', [(350, 230), (150, 180), (100, 130)]),
    ],
    'MLI': [
        ('S', 'OMVS-Sélingué hydro (part Mali)', [(150, 20)], 'hydro'),
        ('S', 'Solaire Mali (Kita, Ségou, Sikasso, Sanankoroba)', [(150, 5)], 'solar'),
        ('S', 'EDM-SA thermique HFO/diesel', [(150, 170), (120, 200), (80, 240)], 'peaker'),
        ('D', 'EDM-SA Demand', [(400, 230), (150, 180), (100, 130)]),
    ],
    'NER': [
        ('S', 'Solaire Niger (Gorou Banda, Niamey, Agadez)', [(60, 5)], 'solar'),
        ('S', 'Charbon Anou Araren', [(18, 90)], 'baseload'),
        ('S', 'NIGELEC diesel/HFO (Gorou Banda, Niamey)', [(80, 190), (60, 230), (40, 270)], 'peaker'),
        ('D', 'NIGELEC Demand', [(200, 230), (80, 180), (50, 130)]),
    ],
    'BEN': [
        ('S', 'Solaire Bénin (Illoulofin)', [(30, 5)], 'solar'),
        ('S', 'CEB Nangbéto (part Bénin)', [(30, 25)], 'hydro'),
        ('S', 'Maria-Gléta', [(100, 110), (27, 130)], 'baseload'),
        ('S', 'Thermique de location', [(50, 170)], 'peaker'),
        ('D', 'SBEE Demand', [(250, 230), (100, 180), (50, 130)]),
    ],
    'TGO': [
        ('S', 'Solaire Togo (Blitta, Dapaong)', [(80, 5)], 'solar'),
        ('S', 'CEB Nangbéto (part Togo)', [(30, 25)], 'hydro'),
        ('S', 'Kékéli CCGT', [(60, 95)], 'baseload'),
        ('S', 'ContourGlobal Lomé', [(60, 125), (40, 150)], 'peaker'),
        ('D', 'CEET Demand', [(200, 230), (70, 180), (40, 130)]),
    ],
    'GIN': [
        ('S', 'Hydro Souapiti-Kaleta-Garafiri', [(500, 12), (350, 22), (100, 35)], 'hydro'),
        ('S', 'EDG thermique HFO (Tombo, Kipé)', [(80, 160), (40, 190)], 'peaker'),
        ('D', 'EDG Demand', [(550, 220), (200, 170), (100, 120)]),
    ],
    'SLE': [
        ('S', 'Hydro Bumbuna', [(45, 20)], 'hydro'),
        ('S', 'Karpowership Sierra Leone', [(60, 130)], 'peaker'),
        ('S', 'EDSA thermique', [(30, 180)], 'peaker'),
        ('D', 'EDSA Demand', [(70, 220), (30, 170), (15, 120)]),
    ],
    'LBR': [
        ('S', 'Hydro Mount Coffee', [(80, 15)], 'hydro'),
        ('S', 'LEC thermique HFO (Bushrod)', [(35, 170)], 'peaker'),
        ('D', 'LEC Demand', [(55, 220), (25, 170), (10, 120)]),
    ],
    'GMB': [
        ('S', 'Solaire Jambur', [(20, 5)], 'solar'),
        ('S', 'NAWEC thermique HFO (Brikama, Kotu)', [(70, 180), (20, 210)], 'peaker'),
        ('D', 'NAWEC Demand', [(80, 230), (30, 180), (15, 130)]),
    ],
    'GNB': [
        ('S', 'Karpowership Guinée-Bissau', [(28, 140)], 'peaker'),
        ('D', 'EAGB Demand', [(40, 230), (15, 180), (8, 130)]),
    ],
}
# "Reference 2024" NTC in MW (values marked (est.) in docs/REFERENCE_DATA.md)
NTC_2024 = {
    ('NGA', 'BEN'): 200, ('NGA', 'NER'): 120, ('BEN', 'TGO'): 300, ('TGO', 'GHA'): 300, ('GHA', 'CIV'): 200,
    ('GHA', 'BFA'): 100, ('CIV', 'BFA'): 100, ('CIV', 'MLI'): 200, ('CIV', 'LBR'): 290, ('LBR', 'SLE'): 290,
    ('SLE', 'GIN'): 290, ('GIN', 'GNB'): 300, ('GNB', 'GMB'): 300, ('GMB', 'SEN'): 300, ('SEN', 'MLI'): 150,
}

# English names of the actors, for the tables of the working paper (the engine and the web platform keep the
# original names). A name absent from this table is already in English.
ACTOR_NAMES_EN = {
    'NIPP et autres centrales gaz': 'NIPP and other gas plants',
    'AKSA et autres OCGT': 'AKSA and other OCGTs',
    'Solaire Ghana': 'Ghana solar',
    'Thermique HFO (Aggreko et autres)': 'HFO plants (Aggreko and others)',
    "Solaire Côte d'Ivoire": "Côte d'Ivoire solar",
    'OMVS Manantali-Félou (part Sénégal)': 'OMVS Manantali-Félou (Senegal share)',
    'Solaire Sénégal': 'Senegal solar',
    "Éolien Taïba N'Diaye": "Taïba N'Diaye wind farm",
    'Charbon Sendou': 'Sendou coal',
    'CCGT gaz (Cap des Biches, Malicounda)': 'Gas CCGT (Cap des Biches, Malicounda)',
    'Thermique HFO (Kounoune, Tobène, Bel-Air)': 'HFO plants (Kounoune, Tobène, Bel-Air)',
    'Solaire Burkina (Zagtouli, Nagréongo, Kodeni, Zina)': 'Burkina Faso solar (Zagtouli, Nagréongo, Kodeni, Zina)',
    'SONABEL thermique HFO': 'SONABEL HFO plants',
    'OMVS-Sélingué hydro (part Mali)': 'OMVS and Sélingué hydro (Mali share)',
    'Solaire Mali (Kita, Ségou, Sikasso, Sanankoroba)': 'Mali solar (Kita, Ségou, Sikasso, Sanankoroba)',
    'EDM-SA thermique HFO/diesel': 'EDM-SA HFO and diesel plants',
    'Solaire Niger (Gorou Banda, Niamey, Agadez)': 'Niger solar (Gorou Banda, Niamey, Agadez)',
    'Charbon Anou Araren': 'Anou Araren coal',
    'NIGELEC diesel/HFO (Gorou Banda, Niamey)': 'NIGELEC diesel and HFO plants (Gorou Banda, Niamey)',
    'Solaire Bénin (Illoulofin)': 'Benin solar (Illoulofin)',
    'CEB Nangbéto (part Bénin)': 'CEB Nangbéto (Benin share)',
    'Thermique de location': 'Rental thermal plants',
    'Solaire Togo (Blitta, Dapaong)': 'Togo solar (Blitta, Dapaong)',
    'CEB Nangbéto (part Togo)': 'CEB Nangbéto (Togo share)',
    'EDG thermique HFO (Tombo, Kipé)': 'EDG HFO plants (Tombo, Kipé)',
    'EDSA thermique': 'EDSA thermal plants',
    'LEC thermique HFO (Bushrod)': 'LEC HFO plant (Bushrod)',
    'Solaire Jambur': 'Jambur solar',
    'NAWEC thermique HFO (Brikama, Kotu)': 'NAWEC HFO plants (Brikama, Kotu)',
    'Karpowership Guinée-Bissau': 'Karpowership Guinea-Bissau',
}


def actor_name_en(name):
    """English name of an actor of the reference case (the name itself when it is already in English)."""
    return ACTOR_NAMES_EN.get(name, name)


def reference_2024_rows(zones=None):
    """Engine rows for the "Reference 2024" set."""
    sup, dem = [], []
    for z, items in REFERENCE_2024.items():
        if zones is not None and z not in zones:
            continue
        for it in items:
            if it[0] == 'S':
                _, name, segs, prof = it
                for k, (q, p) in enumerate(segs):
                    sup.append(dict(zone=z, player='Référence 2024', actor=name, segment=k, quantity=q, price=p, profile=prof))
            else:
                _, name, segs = it
                for k, (q, p) in enumerate(segs):
                    dem.append(dict(zone=z, player='Référence 2024', actor=name, segment=k, quantity=q, price=p))
    return sup, dem

# Gas-fired plants of the 2024 case (exact names of REFERENCE_2024), made more expensive by the "expensive gas"
# variant. Explicit list, drawn from the cost ranges of docs/REFERENCE_DATA.md (section 3): a plant is listed when its
# price was set within the "gas" range of its country. The search for "ccgt / gaz / gas" in the names, used before,
# missed Egbin, Sunon Asogli, CIPREL, AKSA and Karpowership Ghana.
# Excluded: ContourGlobal Lomé (price in the fuel oil range) and Maria-Gléta (fuel to be confirmed).
GAS_PLANTS_2024 = {
    'Egbin', 'Azura-Edo CCGT', 'Okpai CCGT', 'NIPP et autres centrales gaz',                # NGA
    'CCGT TICO-Cenpower-Amandi', 'Sunon Asogli', 'AKSA et autres OCGT', 'Karpowership Ghana',  # GHA
    'Azito CCGT', 'CIPREL', 'Atinkou CCGT',                                                  # CIV
    'CCGT gaz (Cap des Biches, Malicounda)',                                                  # SEN
    'Kékéli CCGT',                                                                            # TGO
}

SCENARIOS = {
    'reference_2024': {
        'fr': ('Référence 2024 (sources publiques)', "Scénario de base : capacités disponibles, pointes de demande, coûts par technologie et capacités des lignes d'après des sources publiques 2023-2025 ; estimations signalées dans docs/fr/DONNEES_DE_REFERENCE.md."),
        'en': ('Reference 2024 (public sources)', "Base scenario: available capacities, peak demands, costs by technology and line capacities from public 2023-2025 sources; estimates flagged in docs/REFERENCE_DATA.md."),
    },
    'secheresse_hydro': {
        'fr': ('Sécheresse hydraulique', "Variante du scénario 2024 : disponibilité des centrales hydrauliques réduite de moitié (Kainji, Akosombo, Soubré, Souapiti, Manantali, Nangbéto…)."),
        'en': ('Hydro drought', "Variant of the 2024 scenario: hydro plants' availability halved (Kainji, Akosombo, Soubré, Souapiti, Manantali, Nangbéto…)."),
    },
    'ligne_nga_ben': {
        'fr': ('Ligne Nigeria–Bénin indisponible', "Variante du scénario 2024 : capacité Nigeria→Bénin à zéro, le Nigeria n'alimente plus que le Niger."),
        'en': ('Nigeria–Benin line out of service', "Variant of the 2024 scenario: Nigeria→Benin capacity set to zero, Nigeria only feeds Niger."),
    },
    'gaz_cher': {
        'fr': ('Gaz cher', "Variante du scénario 2024 : prix des centrales à gaz majorés de 40 %."),
        'en': ('Expensive gas', "Variant of the 2024 scenario: gas-fired plants' prices raised by 40%."),
    },
    'forte_demande': {
        'fr': ('Forte demande', "Variante du scénario 2024 : quantités demandées majorées de 15 % dans toutes les zones."),
        'en': ('High demand', "Variant of the 2024 scenario: demand quantities raised by 15% in all zones."),
    },
    'reference': {   # historical test set, absent from the lists offered to trainers (hidden)
        'fr': ('Jeu de test (Livrable 2)', "Données synthétiques du Livrable 2, conservées pour les tests de non-régression."),
        'en': ('Test set (Livrable 2)', "Synthetic Livrable 2 data, kept for regression tests."),
        'hidden': True,
    },
}



def scenario_rows(key='reference_2024', zones=None):
    """(supply_rows, demand_rows, {(u, v): mw}) for scenario `key`, restricted to `zones` when given.
    A single base set (Reference 2024); the teaching variants change one element only.
    `reference` is the synthetic Deliverable 2 set, kept for the tests."""
    if key not in SCENARIOS:
        raise KeyError(f"Unknown scenario: {key}")
    if key == 'reference':
        sup, dem = default_rows(zones)
        return sup, dem, dict(NTC)     # explicit default NTC: the result does not depend on the database
    sup, dem = reference_2024_rows(zones)
    ntc = dict(NTC_2024)
    if key == 'secheresse_hydro':
        for r in sup:
            if r['profile'] == 'hydro':
                r['quantity'] = round(r['quantity'] * 0.5)
    elif key == 'ligne_nga_ben':
        ntc[('NGA', 'BEN')] = 0.0
    elif key == 'gaz_cher':
        for r in sup:
            if r['actor'] in GAS_PLANTS_2024:
                r['price'] = min(P_MAX, round(r['price'] * 1.4))
    elif key == 'forte_demande':
        for r in dem:
            r['quantity'] = round(r['quantity'] * 1.15)
    return sup, dem, ntc


def scenario_list(lang='fr', include_hidden=False):
    """Scenarios offered to trainers, in menu order (the test set is hidden unless requested)."""
    return [{'key': k, 'name': v.get(lang, v['fr'])[0], 'description': v.get(lang, v['fr'])[1]}
            for k, v in SCENARIOS.items() if include_hidden or not v.get('hidden')]


# ── Complex-order scenario of the working paper (R5) ──────────────
# Hypothetical actors and first-guess values added to the 2024 reference case, to show how the market handles
# every type of complex order together: simple sell and buy blocks, a family of linked buy blocks (the second and
# third potlines of a smelter can only run if the first one does), an exclusive group (a desalination plant chooses
# one of three schedules) and minimum income conditions on three existing producers. Not offered to trainers.
COMPLEX_ORDERS_PLAYER = 'Scenario R5'
# zone, name, side, MW, price, first hour, last hour, parent, exclusive group, kind (for the tables of the paper)
COMPLEX_ORDERS_BLOCKS = [
    ('GHA', 'Gas peaker', 'S', 150, 110, 18, 21, None, None, 'sell block'),
    ('NGA', 'Evening gas plant', 'S', 200, 60, 17, 22, None, None, 'sell block'),
    ('SEN', 'Evening engine plant (HFO)', 'S', 80, 130, 18, 22, None, None, 'sell block'),
    ('MLI', 'Mining load', 'D', 60, 180, 6, 18, None, None, 'buy block'),
    ('CIV', 'Data centre', 'D', 50, 200, 0, 23, None, None, 'buy block'),
    ('NGA', 'Cement plant', 'D', 150, 90, 8, 16, None, None, 'buy block'),
    ('GIN', 'Smelter potline 1', 'D', 150, 110, 0, 23, None, None, 'family: parent'),
    ('GIN', 'Smelter potline 2', 'D', 100, 95, 0, 23, 'Smelter potline 1', None, 'family: child'),
    ('GIN', 'Smelter potline 3 (night)', 'D', 100, 70, 0, 6, 'Smelter potline 1', None, 'family: child'),
    ('SEN', 'Desalination A (all day)', 'D', 40, 140, 0, 23, None, 'Desalination', 'exclusive'),
    ('SEN', 'Desalination B (night)', 'D', 80, 120, 0, 6, None, 'Desalination', 'exclusive'),
    ('SEN', 'Desalination C (day)', 'D', 70, 125, 10, 16, None, 'Desalination', 'exclusive'),
]
# zone, actor of the 2024 case, fixed term (USD), variable term (USD/MWh)
COMPLEX_ORDERS_MIC = [('GHA', 'Karpowership Ghana', 60000, 100),
                      ('SEN', 'Thermique HFO (Kounoune, Tobène, Bel-Air)', 40000, 130),
                      ('TGO', 'Kékéli CCGT', 8000, 90)]


def complex_orders_rows():
    """(block_rows, mic_rows) of the complex-order scenario, in the row format of run_clearing; to be added to
    scenario_rows('reference_2024')."""
    blocks = [dict(zone=z, player=COMPLEX_ORDERS_PLAYER, name=n, side=sd, quantity=q, price=p, h_start=h0, h_end=h1,
                   parent_name=par, excl_group=g) for z, n, sd, q, p, h0, h1, par, g, _ in COMPLEX_ORDERS_BLOCKS]
    mic = [dict(zone=z, player='Référence 2024', actor=a, fixed_term=f, variable_term=v)
           for z, a, f, v in COMPLEX_ORDERS_MIC]
    return blocks, mic
