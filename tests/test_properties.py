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
            names = []
            for b in range(rng.randint(1, 4)):
                h0 = rng.randint(0, 22); h1 = rng.randint(h0, 23)
                side = rng.choice(['S', 'D'])
                row = dict(zone=z, player=player, name=f"Blk{z}{b}", side=side, quantity=rng.choice([10, 50, 100, 250]),
                           price=rng.choice([5, 30, 45, 80, 120, 180, 300]), h_start=h0, h_end=h1)
                if names and rng.random() < 0.4:
                    row['parent_name'] = rng.choice(names)          # linked block
                if rng.random() < 0.3:
                    row['excl_group'] = rng.choice(['G1', 'G2'])     # exclusive group
                blocks.append(row); names.append(row['name'])
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
    # Zero quantity, prices at the bounds, block outside the simulated hours, missing parent, single-member group, MIC without acceptance.
    # Reminder: an all-or-nothing block larger than an isolated zone's demand is rightly rejected (PRB status).
    sup = [dict(zone='NGA', player='a', actor='A', segment=0, quantity=0, price=0, profile='solar'),
           dict(zone='NGA', player='a', actor='B', segment=0, quantity=100, price=300, profile='peaker')]
    dem = [dict(zone='NGA', player='b', actor='L', segment=0, quantity=100, price=500)]
    blocks = [dict(zone='NGA', player='c', name='Nuit', side='S', quantity=20, price=1, h_start=0, h_end=3),
              dict(zone='NGA', player='c', name='Orphelin', side='S', quantity=60, price=1, h_start=12, h_end=12, parent_name='Inconnu'),
              dict(zone='NGA', player='c', name='Seul', side='D', quantity=10, price=400, h_start=12, h_end=12, excl_group='X')]
    mic = [dict(zone='NGA', player='a', actor='A', fixed_term=1e6, variable_term=0)]
    res = run_clearing(sup, dem, block_rows=blocks, mic_rows=mic, hours=[12], ntc_override={k: 0 for k in C.NTC})
    assert not verify_result(res)
    st = {b['name']: b for b in res['summary']['blocks']}
    assert st['Nuit']['status'] == 'inactive' and st['Orphelin']['accepted'] and st['Seul']['accepted']
    assert res['summary']['mic'][0]['satisfied'] and not res['summary']['mic'][0]['withdrawn']
    with pytest.raises(ClearingError):
        run_clearing([dict(zone='NGA', player='a', actor='A', segment=0, quantity=1, price=-1)], [], horizon=1)
