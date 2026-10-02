"""
Scénarios pédagogiques : variantes des données de référence du Livrable 2.
Chaque scénario renvoie (offres de vente, offres d'achat, NTC surchargées) au format des lignes du moteur ;
il sert à compléter les zones sans soumission et à la démonstration.
"""
from .clearing import default_rows, P_MAX

GAS_PLANTS = {'Egbin Gas', 'Delta Gas', 'Geregu', 'Afam VI', 'Olorunsogo', 'Sunon Asogli', 'Cenpower',
              'Karpowership GHA', 'CIPREL', 'Azito', 'Aggreko CIV', 'ContourGlobal'}

SCENARIOS = {
    'reference': {
        'fr': ('Référence', "Données de référence du Livrable 2 : profils types, NTC estimées."),
        'en': ('Reference', "Livrable 2 reference data: typical profiles, estimated NTC."),
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
