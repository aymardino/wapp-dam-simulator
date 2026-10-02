"""
Tests de non-régression du moteur de clearing.
Valeurs de référence : Livrable 2 (8 mars 2026) et notebook wapp_market_clearing_final1.ipynb.
Exécution : pytest -q
"""
import os, sys, tempfile
os.environ['WAPP_DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'test_market.db')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from engine import clearing as C
from engine.clearing import run_clearing, ClearingError, default_rows

# Blocs du Livrable 2, tableau 14 (step 4)
BLOCKS_STEP4 = [
    dict(zone='NGA', player='t', name='NGA Baseload Block', side='S', quantity=300, price=35,  h_start=0,  h_end=23),
    dict(zone='GHA', player='t', name='GHA Night Block',    side='S', quantity=150, price=28,  h_start=0,  h_end=5),
    dict(zone='CIV', player='t', name='CIV Day Block',      side='S', quantity=200, price=42,  h_start=8,  h_end=19),
    dict(zone='BFA', player='t', name='BFA Peak Block',     side='D', quantity=100, price=180, h_start=17, h_end=21),
    dict(zone='SEN', player='t', name='SEN Day Block',      side='D', quantity=200, price=160, h_start=8,  h_end=17),
    dict(zone='NGA', player='t', name='NGA Industry Block', side='D', quantity=500, price=120, h_start=6,  h_end=21),
]
# Blocs liés et exclusifs du Livrable 2, tableau 15 (step 5)
BLOCKS_STEP5 = [
    dict(zone='NGA', player='t', name='NGA Base Parent',   side='S', quantity=400, price=32,  h_start=0,  h_end=23),
    dict(zone='NGA', player='t', name='NGA Extra Child 1', side='S', quantity=200, price=38,  h_start=8,  h_end=19, parent_name='NGA Base Parent'),
    dict(zone='NGA', player='t', name='NGA Extra Child 2', side='S', quantity=100, price=45,  h_start=10, h_end=15, parent_name='NGA Base Parent'),
    dict(zone='GHA', player='t', name='GHA Parent Buy',    side='D', quantity=300, price=170, h_start=7,  h_end=21),
    dict(zone='GHA', player='t', name='GHA Peak Child',    side='D', quantity=150, price=190, h_start=17, h_end=20, parent_name='GHA Parent Buy'),
    dict(zone='CIV', player='t', name='CIV Option A',      side='S', quantity=250, price=40,  h_start=8,  h_end=17, excl_group='CIV'),
    dict(zone='CIV', player='t', name='CIV Option B',      side='S', quantity=400, price=48,  h_start=6,  h_end=21, excl_group='CIV'),
    dict(zone='CIV', player='t', name='CIV Option C',      side='S', quantity=150, price=35,  h_start=10, h_end=13, excl_group='CIV'),
]


@pytest.fixture(scope='module')
def ref():
    return run_clearing(None, None, horizon=24)


def test_step3_reference_values(ref):
    """Step 3 du Livrable 2 : welfare et volume identiques au notebook."""
    assert round(ref['welfare']) == 22_317_910
    assert round(ref['volume']) == 167_900
    assert ref['summary']['n_supply'] == 64 and ref['summary']['n_demand'] == 44


def test_prices_are_admissible(ref):
    """P2 complet : aucun ordre simple paradoxal, aucune divergence de prix sans congestion."""
    d = ref['summary']['diagnostics']
    assert d['pricing_feasible'] and d['tie_break'] == 'exact'
    assert d['pro'] == 0 and d['pao'] == 0 and d['unsaturated_price_gaps'] == 0


def test_welfare_identity(ref):
    """Welfare = surplus consommateur + surplus producteur + rente de congestion."""
    assert abs(ref['summary']['diagnostics']['welfare_identity_gap']) < 1.0


def test_prices_within_bounds(ref):
    for z, series in ref['prices'].items():
        for p in series.values():
            assert C.P_MIN <= p <= C.P_MAX


def test_ntc_override_is_applied():
    res = run_clearing(None, None, horizon=24, ntc_override={k: 0 for k in C.NTC})
    assert sum(abs(v) for f in res['flows'].values() for v in f.values()) == 0
    assert res['welfare'] < 22_317_910


def test_fill_missing_zones():
    sup = [dict(zone='SEN', player='x', actor='SENELEC Thermal', segment=0, quantity=200, price=100, profile='baseload')]
    dem = [dict(zone='SEN', player='x', actor='SENELEC Demand', segment=0, quantity=350, price=200)]
    r_fill = run_clearing(sup, dem, horizon=24, fill_missing_zones=True)
    r_part = run_clearing(sup, dem, horizon=24, fill_missing_zones=False)
    # SEN de référence : 5 segments de vente et 3 d'achat remplacés par 1 et 1
    assert r_fill['summary']['n_supply'] == 64 - 5 + 1
    assert r_fill['summary']['n_demand'] == 44 - 3 + 1
    assert r_part['summary']['n_supply'] == 1 and r_part['summary']['n_demand'] == 1


def test_blocks_step4_reference():
    """Step 4 du Livrable 2 : 5 blocs acceptés sur 6, NGA Industry paradoxalement rejeté (toléré)."""
    res = run_clearing(None, None, horizon=24, block_rows=BLOCKS_STEP4)
    assert round(res['welfare']) == 23_082_419
    acc = {b['name']: b['accepted'] for b in res['summary']['blocks']}
    assert acc == {'NGA Baseload Block': True, 'GHA Night Block': True, 'CIV Day Block': True,
                   'BFA Peak Block': True, 'SEN Day Block': True, 'NGA Industry Block': False}
    status = {b['name']: b['status'] for b in res['summary']['blocks']}
    assert status['NGA Industry Block'] == 'PRB'
    assert res['summary']['diagnostics']['pab'] == []
    assert res['summary']['diagnostics']['pro'] == 0 and res['summary']['diagnostics']['pao'] == 0


def test_linked_exclusive_step5_reference():
    """Step 5 du Livrable 2 : enfants acceptés avec leur parent, une seule option exclusive retenue."""
    res = run_clearing(None, None, horizon=24, block_rows=BLOCKS_STEP5)
    assert round(res['welfare']) == 23_775_223
    acc = {b['name']: b['accepted'] for b in res['summary']['blocks']}
    assert acc['NGA Base Parent'] and acc['NGA Extra Child 1'] and acc['NGA Extra Child 2']
    assert acc['GHA Parent Buy'] and acc['GHA Peak Child']
    assert acc['CIV Option B'] and not acc['CIV Option A'] and not acc['CIV Option C']


def test_child_rejected_when_parent_rejected():
    """Un enfant ne peut pas être accepté sans son parent, même s'il est rentable seul."""
    blocks = [
        dict(zone='NGA', player='t', name='Parent cher', side='S', quantity=100, price=400, h_start=0, h_end=23),
        dict(zone='NGA', player='t', name='Enfant pas cher', side='S', quantity=100, price=1, h_start=0, h_end=23, parent_name='Parent cher'),
    ]
    res = run_clearing(None, None, horizon=24, block_rows=blocks)
    acc = {b['name']: b['accepted'] for b in res['summary']['blocks']}
    assert not acc['Parent cher'] and not acc['Enfant pas cher']


def test_single_hour_mode():
    res = run_clearing(None, None, hours=[19])
    assert list(res['prices']['NGA'].keys()) == ['19']
    assert res['summary']['hours'] == [19] and res['summary']['horizon'] == 1
    assert len(res['dispatch']['demand']) == 1


def test_price_out_of_bounds_raises():
    sup = [dict(zone='NGA', player='x', actor='A', segment=0, quantity=100, price=600, profile='baseload')]
    dem = [dict(zone='NGA', player='y', actor='B', segment=0, quantity=100, price=200)]
    with pytest.raises(ClearingError):
        run_clearing(sup, dem, horizon=1)


def test_unknown_zone_raises():
    with pytest.raises(ClearingError):
        run_clearing([dict(zone='XXX', player='x', actor='A', segment=0, quantity=1, price=1)], [], horizon=1)


def test_no_trade_market_has_consistent_price():
    """Marché sans échange : prix entre la meilleure demande et la meilleure offre, volume nul."""
    sup = [dict(zone='NGA', player='x', actor='A', segment=0, quantity=100, price=150, profile='baseload')]
    dem = [dict(zone='NGA', player='y', actor='B', segment=0, quantity=100, price=100)]
    res = run_clearing(sup, dem, horizon=1)
    assert res['volume'] == 0
    assert 100 <= res['prices']['NGA']['0'] <= 150
    assert 0 in res['summary']['zones']['NGA']['no_trade_hours']


def test_l2_pricing_mode_still_available():
    res = run_clearing(None, None, horizon=24, pricing='l2')
    assert res['summary']['diagnostics']['pricing_mode'] == 'l2'
    assert round(res['welfare']) == 22_317_910


def test_actor_results_consistent(ref):
    actors = ref['summary']['actors']
    assert actors, "résultats par acteur attendus"
    tcn = [a for a in actors if a['actor'] == 'TCN Nigeria' and a['side'] == 'D'][0]
    assert tcn['accepted_mwh'] > 0 and tcn['avg_price'] is not None
    total_supply = sum(a['accepted_mwh'] for a in actors if a['side'] == 'S')
    assert abs(total_supply - ref['volume']) < 5
