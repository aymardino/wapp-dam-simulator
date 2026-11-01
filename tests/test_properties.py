"""
Property tests: random cases (segments, simple, linked and exclusive blocks, MIC, rules, scenarios, hours)
checked by engine.checks.verify_result. Number of cases: WAPP_PROPERTY_CASES (default 25).
"""
import os, sys, random, tempfile
os.environ.setdefault('WAPP_DB_PATH', os.path.join(tempfile.mkdtemp(), 'props.db'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from engine import clearing as C
from engine.clearing import run_clearing, ClearingError
from engine.checks import verify_result
from engine.scenarios import scenario_rows, SCENARIOS

N_CASES = int(os.environ.get('WAPP_PROPERTY_CASES', '25'))
PROFILES = ['baseload', 'hydro', 'solar', 'peaker', 'flat']


def random_case(rng):
    zones = rng.sample(C.ZONES, rng.randint(1, 6))
    supply, demand, blocks, mic = [], [], [], []
    for z in zones:
        for a in range(rng.randint(0, 3)):
            player = f"P{z}{a}"
            name = f"Gen{z}{a}"
            for k in range(rng.randint(1, 4)):
                supply.append(dict(zone=z, player=player, actor=name, segment=k, quantity=rng.choice([0, 5, 20, 50, 120, 300, 500]),
                                   price=rng.choice([0, 1, 10, 25, 25, 40, 60, 95, 130, 200, 350, 500]), profile=rng.choice(PROFILES)))
            if rng.random() < 0.3:
                mic.append(dict(zone=z, player=player, actor=name, fixed_term=rng.choice([0, 500, 5000, 50000]), variable_term=rng.choice([0, 10, 60])))
        for a in range(rng.randint(0, 2)):
            player = f"D{z}{a}"
            for k in range(rng.randint(1, 3)):
                demand.append(dict(zone=z, player=player, actor=f"Load{z}{a}", segment=k, quantity=rng.choice([0, 10, 50, 150, 400, 1500]),
                                   price=rng.choice([0, 30, 80, 100, 100, 150, 200, 250, 500])))
        if rng.random() < 0.6:
            player = f"B{z}"
            roots = []                                              # MODIFIÉ : 'names' devient 'roots' = blocs sans parent (seuls eux peuvent être parents)
            for b in range(rng.randint(1, 4)):
                h0 = rng.randint(0, 22); h1 = rng.randint(h0, 23)
                side = rng.choice(['S', 'D'])
                row = dict(zone=z, player=player, name=f"Blk{z}{b}", side=side, quantity=rng.choice([10, 50, 100, 250]),
                           price=rng.choice([5, 30, 45, 80, 120, 180, 300]), h_start=h0, h_end=h1)
                if roots and rng.random() < 0.4:                    # MODIFIÉ : 'names' -> 'roots'
                    row['parent_name'] = rng.choice(roots)          # MODIFIÉ : le parent est choisi parmi les blocs sans parent (pas de chaînes)
                else:                                               # AJOUTÉ : un bloc sans parent peut devenir parent d'un bloc suivant
                    roots.append(row['name'])                       # AJOUTÉ
                if rng.random() < 0.3:
                    row['excl_group'] = rng.choice(['G1', 'G2'])     # exclusive group
                blocks.append(row)                                  # MODIFIÉ : '; names.append(row['name'])' supprimé (remplacé par roots.append ci-dessus)
            # AJOUTÉ : un groupe exclusif doit contenir au moins deux blocs ; on retire l'étiquette des groupes d'un seul bloc
            zb = [r for r in blocks if r['player'] == player]       # AJOUTÉ
            for g in ('G1', 'G2'):                                  # AJOUTÉ
                members = [r for r in zb if r.get('excl_group') == g]   # AJOUTÉ
                if len(members) == 1:                               # AJOUTÉ
                    del members[0]['excl_group']                    # AJOUTÉ
    rules = dict(pricing=rng.choice(['complete', 'complete', 'l2']), pab_rule=rng.choice(['euphemia', 'euphemia', 'l2', 'none']),
                 tie_rule=rng.choice(['prorata', 'order', 'solver']))
    hours = None if rng.random() < 0.7 else [rng.randint(0, 23)]
    scenario = rng.choice(list(SCENARIOS))
    fill = rng.random() < 0.6
    ntc = None
    if rng.random() < 0.3:
        ntc = {k: rng.choice([0, 50, v]) for k, v in C.NTC.items()}
    return dict(supply=supply, demand=demand, blocks=blocks, mic=mic, rules=rules, hours=hours, scenario=scenario, fill=fill, ntc=ntc)


@pytest.mark.parametrize('seed', range(N_CASES))
def test_random_case_is_consistent(seed):
    rng = random.Random(1000 + seed)
    case = random_case(rng)
    sup_ref, dem_ref, sc_ntc = scenario_rows(case['scenario'])
    ntc = dict(sc_ntc)
    if case['ntc']:
        ntc.update(case['ntc'])
    if not (case['supply'] or case['demand'] or case['blocks']) and not case['fill']:
        return      # nothing to compute: the API refuses this case upstream
    res = run_clearing(case['supply'], case['demand'], block_rows=case['blocks'], mic_rows=case['mic'], hours=case['hours'],
                       fill_missing_zones=case['fill'], ntc_override=ntc or None, reference_rows=(sup_ref, dem_ref), **case['rules'])
    problems = verify_result(res)
    # Mode 'l2' (Deliverable 2 prices) lacks the complete admissible set: price properties are not imposed on it.
    if case['rules']['pricing'] == 'l2':
        problems = [p for p in problems if not p.startswith('prix')]
    assert not problems, f"seed {seed} : " + " | ".join(problems)


def test_edge_cases():
    # MODIFIÉ : 'missing parent, single-member group' retirés de la liste (ces cas sont maintenant des erreurs, testés plus bas)
    # Zero quantity, prices at the bounds, block outside the simulated hours, MIC without acceptance.
    # Reminder: an all-or-nothing block larger than an isolated zone's demand is rightly rejected (PRB status).
    sup = [dict(zone='NGA', player='a', actor='A', segment=0, quantity=0, price=0, profile='solar'),
           dict(zone='NGA', player='a', actor='B', segment=0, quantity=100, price=300, profile='peaker')]
    dem = [dict(zone='NGA', player='b', actor='L', segment=0, quantity=100, price=500)]
    # MODIFIÉ : blocs 'Orphelin' (parent introuvable) et 'Seul' (groupe d'un seul bloc) supprimés ;
    #           ils provoquent maintenant une ClearingError (voir test_invalid_block_links)
    blocks = [dict(zone='NGA', player='c', name='Nuit', side='S', quantity=20, price=1, h_start=0, h_end=3)]
    mic = [dict(zone='NGA', player='a', actor='A', fixed_term=1e6, variable_term=0)]
    res = run_clearing(sup, dem, block_rows=blocks, mic_rows=mic, hours=[12], ntc_override={k: 0 for k in C.NTC})
    assert not verify_result(res)
    st = {b['name']: b for b in res['summary']['blocks']}
    assert st['Nuit']['status'] == 'inactive'                      # MODIFIÉ : contrôles sur 'Orphelin' et 'Seul' supprimés
    assert res['summary']['mic'][0]['satisfied'] and not res['summary']['mic'][0]['withdrawn']
    with pytest.raises(ClearingError):
        run_clearing([dict(zone='NGA', player='a', actor='A', segment=0, quantity=1, price=-1)], [], horizon=1)


# AJOUTÉ : nouveau test, les liens invalides entre blocs doivent être refusés
def test_invalid_block_links():
    """Parent introuvable, nom en double, bloc parent de lui-même, chaîne, cycle et groupe d'un seul bloc sont refusés."""
    def blk(name, **kw):
        return dict(zone='NGA', player='c', name=name, side='S', quantity=10, price=1, h_start=12, h_end=12, **kw)
    cases = [
        [blk('Orphelin', parent_name='Inconnu')],                                   # parent introuvable
        [blk('A'), blk('A')],                                                       # nom en double
        [blk('A', parent_name='A')],                                                # parent de lui-même
        [blk('Grand-parent'), blk('Parent', parent_name='Grand-parent'),
         blk('Enfant', parent_name='Parent')],                                      # chaîne
        [blk('A', parent_name='B'), blk('B', parent_name='A')],                     # cycle
        [blk('Seul', excl_group='X')],                                              # groupe d'un seul bloc
    ]
    for blocks in cases:
        with pytest.raises(ClearingError):
            run_clearing([], [dict(zone='NGA', player='b', actor='L', segment=0, quantity=100, price=500)],
                         block_rows=blocks, hours=[12], ntc_override={k: 0 for k in C.NTC})


# AJOUTÉ : nouveau test, un parent avec deux enfants reste autorisé
def test_parent_with_two_children_is_allowed():
    """Un parent peut avoir plusieurs enfants (Livrable 2, étape 5)."""
    blocks = [dict(zone='NGA', player='c', name='P', side='S', quantity=50, price=1, h_start=12, h_end=12),
              dict(zone='NGA', player='c', name='E1', side='S', quantity=20, price=2, h_start=12, h_end=12, parent_name='P'),
              dict(zone='NGA', player='c', name='E2', side='S', quantity=20, price=3, h_start=12, h_end=12, parent_name='P')]
    res = run_clearing([], [dict(zone='NGA', player='b', actor='L', segment=0, quantity=100, price=500)],
                       block_rows=blocks, hours=[12], ntc_override={k: 0 for k in C.NTC})
    assert not verify_result(res)



# AJOUTÉ PAR ENRICO (étape 2) : au plus 4 segments par acteur et par côté
def test_max_four_segments_per_actor():
    """Quatre segments sont acceptés, un cinquième est refusé (vente et achat)."""
    def seg(k):
        return dict(zone='NGA', player='a', actor='A', segment=k, quantity=10, price=10 + k, profile='flat')
    dem = [dict(zone='NGA', player='b', actor='L', segment=0, quantity=100, price=500)]
    run_clearing([seg(k) for k in range(4)], dem, hours=[12], ntc_override={k: 0 for k in C.NTC})   # 4 : accepté
    with pytest.raises(ClearingError):
        run_clearing([seg(k) for k in range(5)], dem, hours=[12], ntc_override={k: 0 for k in C.NTC})   # 5 : refusé
    buy = [dict(zone='NGA', player='b', actor='L', segment=k, quantity=10, price=100 - k) for k in range(5)]
    with pytest.raises(ClearingError):
        run_clearing([seg(0)], buy, hours=[12], ntc_override={k: 0 for k in C.NTC})                    # 5 à l'achat : refusé





# AJOUTÉ PAR ENRICO (règle de famille) : un parent en perte, compensé par son enfant, reste accepté
def test_family_rule_parent_supported_by_child():
    """Parent à 40 en perte au prix de 30, enfant à 10 en gain : la famille est rentable, les deux restent acceptés."""
    dem = [dict(zone='NGA', player='b', actor='L', segment=0, quantity=200, price=100)]
    sup = [dict(zone='NGA', player='a', actor='A', segment=0, quantity=150, price=30, profile='flat')]
    blk = [dict(zone='NGA', player='c', name='P', side='S', quantity=50, price=40, h_start=12, h_end=12),
           dict(zone='NGA', player='c', name='E', side='S', quantity=50, price=10, h_start=12, h_end=12, parent_name='P')]
    res = run_clearing(sup, dem, block_rows=blk, hours=[12], ntc_override={k: 0 for k in C.NTC})
    st = {b['name']: b for b in res['summary']['blocks']}
    assert res['prices']['NGA']['12'] == 30.0
    assert st['P']['accepted'] and st['P']['status'] == 'OK' and st['P']['surplus_if_accepted'] < 0
    assert st['E']['accepted'] and st['E']['status'] == 'OK'
    assert st['P']['family_surplus'] > 0



# AJOUTÉ (règle de famille) : même cas sans lien, P n'est plus nécessaire et il est rejeté
def test_same_blocks_without_link():
    """Sans lien parent-enfant, le bloc P à 40 n'est pas retenu ; E à 10 est accepté seul."""
    dem = [dict(zone='NGA', player='b', actor='L', segment=0, quantity=200, price=100)]
    sup = [dict(zone='NGA', player='a', actor='A', segment=0, quantity=150, price=30, profile='flat')]
    blk = [dict(zone='NGA', player='c', name='P', side='S', quantity=50, price=40, h_start=12, h_end=12),
           dict(zone='NGA', player='c', name='E', side='S', quantity=50, price=10, h_start=12, h_end=12)]
    res = run_clearing(sup, dem, block_rows=blk, hours=[12], ntc_override={k: 0 for k in C.NTC})
    st = {b['name']: b for b in res['summary']['blocks']}
    assert res['prices']['NGA']['12'] == 30.0
    assert not st['P']['accepted'] and st['E']['accepted']
    assert st['P']['status'] == 'OK' and st['E']['status'] == 'OK'


    

# AJOUTÉ : le vérificateur détecte des résultats falsifiés (prix, flux)
def test_checker_detects_corrupted_results():
    """On fausse un résultat correct : un prix modifié et un flux de signe inversé doivent être signalés."""
    import copy
    sup, dem, ntc = scenario_rows('reference_2024')
    res = run_clearing(sup, dem, ntc_override=ntc)
    assert not verify_result(res)                                  # le résultat correct passe
    bad = copy.deepcopy(res)
    bad['prices']['NGA']['19'] += 30                               # prix faux au Nigeria à 19 h
    assert any(p.startswith('prix') for p in verify_result(bad))
    bad = copy.deepcopy(res)
    k = next(k for k, s in bad['flows'].items() if abs(s['19']) > 10)
    bad['flows'][k]['19'] = -bad['flows'][k]['19']                 # flux de signe inversé
    assert any(p.startswith('balance') for p in verify_result(bad))