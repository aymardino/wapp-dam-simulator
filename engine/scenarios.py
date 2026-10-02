"""
Scénarios pédagogiques : variantes des données de référence du Livrable 2.
Chaque scénario renvoie (offres de vente, offres d'achat, NTC surchargées) au format des lignes du moteur ;
il sert à compléter les zones sans soumission et à la démonstration.
"""
from .clearing import default_rows, P_MAX

# ── Jeu « Référence 2024 » : capacités disponibles et pointes de demande d'après des sources publiques ──
# Détail et sources : docs/DONNEES_DE_REFERENCE.md. Les valeurs marquées (est.) sont des estimations.
# Format : zone → ('S', nom, [(MW, prix USD/MWh), ...], profil) ou ('D', nom, [(MW, prix max), ...])
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
# NTC « Référence 2024 » en MW (valeurs marquées (est.) dans docs/DONNEES_DE_REFERENCE.md)
NTC_2024 = {
    ('NGA', 'BEN'): 200, ('NGA', 'NER'): 120, ('BEN', 'TGO'): 300, ('TGO', 'GHA'): 300, ('GHA', 'CIV'): 200,
    ('GHA', 'BFA'): 100, ('CIV', 'BFA'): 100, ('CIV', 'MLI'): 200, ('CIV', 'LBR'): 290, ('LBR', 'SLE'): 290,
    ('SLE', 'GIN'): 290, ('GIN', 'GNB'): 300, ('GNB', 'GMB'): 300, ('GMB', 'SEN'): 300, ('SEN', 'MLI'): 150,
}


def reference_2024_rows(zones=None):
    """Lignes du moteur pour le jeu « Référence 2024 »."""
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

GAS_PLANTS = {'Egbin Gas', 'Delta Gas', 'Geregu', 'Afam VI', 'Olorunsogo', 'Sunon Asogli', 'Cenpower',
              'Karpowership GHA', 'CIPREL', 'Azito', 'Aggreko CIV', 'ContourGlobal'}

SCENARIOS = {
    'reference': {
        'fr': ('Référence (Livrable 2)', "Données de référence du Livrable 2 : profils types, NTC estimées d'après les tensions des lignes."),
        'en': ('Reference (Livrable 2)', "Livrable 2 reference data: typical profiles, NTC estimated from line voltages."),
    },
    'reference_2024': {
        'fr': ('Référence 2024 (sources publiques)', "Capacités disponibles, pointes de demande, coûts par technologie et capacités des lignes d'après des sources publiques 2023-2025 ; estimations signalées dans docs/DONNEES_DE_REFERENCE.md."),
        'en': ('Reference 2024 (public sources)', "Available capacities, peak demands, costs by technology and line capacities from public 2023-2025 sources; estimates flagged in docs/DONNEES_DE_REFERENCE.md."),
    },
    'secheresse_hydro': {
        'fr': ('Sécheresse hydraulique', "Disponibilité des centrales hydrauliques réduite de moitié (Akosombo, CI-Energies, Manantali, Félou, Kaleta, Garafiri, Nangbéto)."),
        'en': ('Hydro drought', "Hydro plants' availability halved (Akosombo, CI-Energies, Manantali, Félou, Kaleta, Garafiri, Nangbéto)."),
    },
    'ligne_nga_ben': {
        'fr': ('Ligne Nigeria–Bénin indisponible', "NTC Nigeria→Bénin à zéro : le corridor est coupe le Nigeria du reste du réseau."),
        'en': ('Nigeria–Benin line out of service', "Nigeria→Benin NTC set to zero: the eastern corridor cuts Nigeria off from the rest of the network."),
    },
    'gaz_cher': {
        'fr': ('Gaz cher', "Prix des centrales à gaz et des unités de pointe thermiques majorés de 40 %."),
        'en': ('Expensive gas', "Gas-fired and thermal peaking plants' prices raised by 40%."),
    },
    'forte_demande': {
        'fr': ('Forte demande', "Quantités demandées majorées de 15 % dans toutes les zones."),
        'en': ('High demand', "Demand quantities raised by 15% in all zones."),
    },
}


def scenario_rows(key='reference', zones=None):
    """(supply_rows, demand_rows, {(u, v): mw}) pour le scénario `key`, limité aux `zones` si fournies."""
    if key not in SCENARIOS:
        raise KeyError(f"Scénario inconnu : {key}")
    if key == 'reference_2024':
        sup, dem = reference_2024_rows(zones)
        return sup, dem, dict(NTC_2024)
    sup, dem = default_rows(zones)
    ntc = {}
    if key == 'secheresse_hydro':
        for r in sup:
            if r['profile'] == 'hydro':
                r['quantity'] = round(r['quantity'] * 0.5)
    elif key == 'ligne_nga_ben':
        ntc[('NGA', 'BEN')] = 0.0
    elif key == 'gaz_cher':
        for r in sup:
            if r['actor'] in GAS_PLANTS:
                r['price'] = min(P_MAX, round(r['price'] * 1.4))
    elif key == 'forte_demande':
        for r in dem:
            r['quantity'] = round(r['quantity'] * 1.15)
    return sup, dem, ntc


def scenario_list(lang='fr'):
    return [{'key': k, 'name': v.get(lang, v['fr'])[0], 'description': v.get(lang, v['fr'])[1]} for k, v in SCENARIOS.items()]
