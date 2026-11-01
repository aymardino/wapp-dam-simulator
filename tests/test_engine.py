"""
Regression tests of the clearing engine.
Reference values: Deliverable 2 (8 March 2026) and the notebook wapp_market_clearing_final1.ipynb.
Run: pytest -q
"""
import os, sys, tempfile
os.environ['WAPP_DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'test_market.db')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from engine import clearing as C
from engine.clearing import run_clearing, ClearingError, default_rows

# Deliverable 2 blocks, table 14 (step 4)
BLOCKS_STEP4 = [
    dict(zone='NGA', player='t', name='NGA Baseload Block', side='S', quantity=300, price=35,  h_start=0,  h_end=23),
    dict(zone='GHA', player='t', name='GHA Night Block',    side='S', quantity=150, price=28,  h_start=0,  h_end=5),
    dict(zone='CIV', player='t', name='CIV Day Block',      side='S', quantity=200, price=42,  h_start=8,  h_end=19),
    dict(zone='BFA', player='t', name='BFA Peak Block',     side='D', quantity=100, price=180, h_start=17, h_end=21),
    dict(zone='SEN', player='t', name='SEN Day Block',      side='D', quantity=200, price=160, h_start=8,  h_end=17),
    dict(zone='NGA', player='t', name='NGA Industry Block', side='D', quantity=500, price=120, h_start=6,  h_end=21),
]
# Deliverable 2 linked and exclusive blocks, table 15 (step 5)
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
    """Deliverable 2 step 3: welfare and volume identical to the notebook."""
    assert round(ref['welfare']) == 22_317_910
    assert round(ref['volume']) == 167_900
    assert ref['summary']['n_supply'] == 64 and ref['summary']['n_demand'] == 44


def test_prices_are_admissible(ref):
    """Complete P2: no paradoxical simple order, no price divergence without congestion."""
    d = ref['summary']['diagnostics']
    assert d['pricing_feasible'] and d['tie_break'] == 'exact'
    assert d['pro'] == 0 and d['pao'] == 0 and d['unsaturated_price_gaps'] == 0


def test_welfare_identity(ref):
    """Welfare = consumer surplus + producer surplus + congestion rent."""
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
    # reference SEN: 5 sell segments and 3 buy segments replaced by 1 and 1
    assert r_fill['summary']['n_supply'] == 64 - 5 + 1
    assert r_fill['summary']['n_demand'] == 44 - 3 + 1
    assert r_part['summary']['n_supply'] == 1 and r_part['summary']['n_demand'] == 1


def test_blocks_step4_reference():
    """Deliverable 2 step 4: 5 blocks accepted out of 6, NGA Industry paradoxically rejected (tolerated)."""
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
    """Deliverable 2 step 5: children accepted with their parent, a single exclusive option kept."""
    res = run_clearing(None, None, horizon=24, block_rows=BLOCKS_STEP5)
    assert round(res['welfare']) == 23_775_223
    acc = {b['name']: b['accepted'] for b in res['summary']['blocks']}
    assert acc['NGA Base Parent'] and acc['NGA Extra Child 1'] and acc['NGA Extra Child 2']
    assert acc['GHA Parent Buy'] and acc['GHA Peak Child']
    assert acc['CIV Option B'] and not acc['CIV Option A'] and not acc['CIV Option C']


def test_child_rejected_when_parent_rejected():
    """A child cannot be accepted without its parent, even when profitable on its own."""
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
    """Market without trade: price between the best bid and the best offer, zero volume."""
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


# ── Equal-price sharing and Minimum Income Condition ──────────────
NTC_ZERO = {k: 0 for k in C.NTC}   # isolates every zone


def _one_zone(supply, demand, **kw):
    return run_clearing(supply, demand, hours=[12], ntc_override=NTC_ZERO, **kw)


def test_worked_examples_of_indeterminate_prices():
    """The three single-hour cases of the working paper (network reduced to the zones involved)."""
    def S(zone, q, p): return dict(zone=zone, player='s', actor='Seller', segment=0, quantity=q, price=p, profile='flat')
    def D(zone, q, p): return dict(zone=zone, player='d', actor='Buyer', segment=0, quantity=q, price=p)
    def run(sup, dem, ntc=None, **kw):
        return run_clearing(sup, dem, hours=[19], ntc_override={**NTC_ZERO, **(ntc or {})}, **kw)   # load profile = 1.00 at 19:00
    # (a) no marginal order: any price in [20, 80] is admissible, the midpoint is published
    assert run([S('GHA', 50, 20)], [D('GHA', 50, 80)])['prices']['GHA']['19'] == 50
    assert run([S('GHA', 100, 20)], [D('GHA', 50, 80)])['prices']['GHA']['19'] == 20      # partial sell: the price is unique
    # (b) saturated line: the importing zone takes the midpoint of its local interval [0, 100]
    line = {('NGA', 'BEN'): 200}
    res = run([S('NGA', 1000, 20)], [D('BEN', 200, 100)], line)
    assert (res['prices']['NGA']['19'], res['prices']['BEN']['19'], res['flows']['NGA->BEN']['19']) == (20, 50, 200)
    assert res['summary']['congestion_rent'] == 6000
    assert run([S('NGA', 1000, 20)], [D('BEN', 300, 100)], line)['prices']['BEN']['19'] == 100   # partial buy sets the price
    # (c) no trade: midpoint between the rejected buy and the rejected sell
    res = run([S('GHA', 50, 90)], [D('GHA', 50, 30)])
    assert res['volume'] == 0 and res['prices']['GHA']['19'] == 60
    # the rule restricted to accepted orders has no information here: midpoint of the price bounds, one paradoxical rejection
    res = run([S('GHA', 50, 90)], [D('GHA', 50, 30)], pricing='l2')
    assert res['prices']['GHA']['19'] == 250 and res['summary']['diagnostics']['pro'] == 1


def test_tie_rule_prorata_shares_equal_price_offers():
    sup = [dict(zone='NGA', player='a', actor='A', segment=0, quantity=100, price=50, profile='baseload'),
           dict(zone='NGA', player='b', actor='B', segment=0, quantity=100, price=50, profile='baseload')]
    dem = [dict(zone='NGA', player='c', actor='TCN', segment=0, quantity=150, price=100)]
    res = _one_zone(sup, dem)                                   # pro rata by default
    acc = {a['actor']: a['accepted_mwh'] for a in res['summary']['actors'] if a['side'] == 'S'}
    assert abs(acc['A'] - acc['B']) < 0.2, acc                  # 132 MWh demanded, 95 + 95 offered: 66 each
    assert res['prices']['NGA']['12'] == 50
    assert res['summary']['diagnostics']['tie_groups_adjusted'] >= 0
    res_o = _one_zone(sup, dem, tie_rule='order')
    acc_o = {a['actor']: a['accepted_mwh'] for a in res_o['summary']['actors'] if a['side'] == 'S'}
    assert acc_o['A'] == 95 and abs(acc_o['B'] - 37) < 0.2, acc_o   # first served
    assert round(res_o['welfare']) == round(res['welfare']) and round(res_o['volume']) == round(res['volume'])


def test_mic_withdraws_actor_and_reruns():
    sup = [dict(zone='NGA', player='a', actor='Base', segment=0, quantity=100, price=30, profile='baseload'),
           dict(zone='NGA', player='b', actor='Peaker', segment=0, quantity=100, price=60, profile='baseload')]
    dem = [dict(zone='NGA', player='c', actor='TCN', segment=0, quantity=150, price=100)]
    mic = [dict(zone='NGA', player='b', actor='Peaker', fixed_term=3000, variable_term=0)]
    res0 = _one_zone(sup, dem)
    assert res0['prices']['NGA']['12'] == 60                     # marginal peaker: 37 MWh at 60 = 2,220 < 3,000
    res = _one_zone(sup, dem, mic_rows=mic)
    d = res['summary']['diagnostics']
    assert d['mic_iterations'] == 2 and d['mic_withdrawn'] == ['Peaker (NGA)']
    assert res['prices']['NGA']['12'] == 100                     # demand becomes marginal
    m = res['summary']['mic'][0]
    assert m['withdrawn'] is True and m['satisfied'] is False
    peaker = [a for a in res['summary']['actors'] if a['actor'] == 'Peaker'][0]
    assert peaker['status'] == 'withdrawn_mic' and peaker['accepted_mwh'] == 0
    assert round(res['volume']) == 95


def test_mic_satisfied_keeps_actor():
    sup = [dict(zone='NGA', player='a', actor='Base', segment=0, quantity=100, price=30, profile='baseload'),
           dict(zone='NGA', player='b', actor='Peaker', segment=0, quantity=100, price=60, profile='baseload')]
    dem = [dict(zone='NGA', player='c', actor='TCN', segment=0, quantity=150, price=100)]
    mic = [dict(zone='NGA', player='b', actor='Peaker', fixed_term=1000, variable_term=20)]   # 1000 + 20×37 = 1,740 ≤ 2,220
    res = _one_zone(sup, dem, mic_rows=mic)
    m = res['summary']['mic'][0]
    assert m['satisfied'] is True and not m['withdrawn'] and res['summary']['diagnostics']['mic_iterations'] == 1
    assert abs(m['income'] - 2220) < 1

#nouveau, ajouté par ENRICO parce que les MIC sont seulement sur les segments
def test_mic_does_not_apply_to_blocks():
    """MODIFIÉ : comme dans EUPHEMIA, une MIC porte sur les segments de vente ; les blocs du même
    participant ne sont ni comptés ni retirés."""
    sup = [dict(zone='NGA', player='b', actor='Peaker', segment=0, quantity=50, price=60, profile='baseload')]
    dem = [dict(zone='NGA', player='c', actor='TCN', segment=0, quantity=400, price=100)]
    blocks = [dict(zone='NGA', player='b', name='Parent', side='S', quantity=50, price=60, h_start=12, h_end=12),
              dict(zone='NGA', player='b', name='Enfant', side='S', quantity=50, price=61, h_start=12, h_end=12, parent_name='Parent')]
    mic = [dict(zone='NGA', player='b', actor='Peaker', fixed_term=100000, variable_term=0)]
    res = run_clearing(sup, dem, hours=[12], ntc_override=NTC_ZERO, block_rows=blocks, mic_rows=mic)
    assert res['summary']['diagnostics']['mic_withdrawn'] == ['Peaker (NGA)']   # le segment est retiré
    st = {b['name']: b for b in res['summary']['blocks']}
    assert st['Parent']['accepted'] and st['Enfant']['accepted']               # les blocs restent sur le marché

#nouveau, ajouté par ENRICO parce que les MIC sont seulement sur les segments
def test_invalid_mic_refused():
    """AJOUTÉ : MIC sans segment de vente (par exemple portée par un bloc) ou avec un terme négatif : refusée."""
    sup = [dict(zone='NGA', player='a', actor='Base', segment=0, quantity=100, price=30, profile='baseload')]
    dem = [dict(zone='NGA', player='c', actor='TCN', segment=0, quantity=150, price=100)]
    blocks = [dict(zone='NGA', player='b', name='Bloc', side='S', quantity=50, price=60, h_start=12, h_end=12)]
    for mic in ([dict(zone='NGA', player='b', actor='Bloc', fixed_term=1000, variable_term=0)],     # bloc
                [dict(zone='NGA', player='a', actor='Base', fixed_term=-1, variable_term=0)],      # terme négatif
                [dict(zone='NGA', player='a', actor='Base', fixed_term=0, variable_term=-5)]):     # terme négatif
        with pytest.raises(ClearingError):
            run_clearing(sup, dem, hours=[12], ntc_override=NTC_ZERO, block_rows=blocks, mic_rows=mic)



def test_reference_zones_reported(ref):
    assert ref['summary']['reference_zones'] == C.ZONES
    sup = [dict(zone='SEN', player='x', actor='A', segment=0, quantity=10, price=10, profile='baseload')]
    r = run_clearing(sup, [], horizon=1, fill_missing_zones=True)
    assert 'SEN' not in r['summary']['reference_zones'] and len(r['summary']['reference_zones']) == 13
    r2 = run_clearing(sup, [], horizon=1, fill_missing_zones=False)
    assert r2['summary']['reference_zones'] == []


def test_scenarios_change_outcomes():
    from engine.scenarios import scenario_rows, SCENARIOS, scenario_list
    assert set(scenario_list('en')[0].keys()) == {'key', 'name', 'description'} and len(SCENARIOS) == 6
    assert [x['key'] for x in scenario_list('fr')] == ['reference_2024', 'secheresse_hydro', 'ligne_nga_ben', 'gaz_cher', 'forte_demande']   # Deliverable 2 set hidden
    assert len(scenario_list('fr', include_hidden=True)) == 6
    sup0, dem0, ntc0 = scenario_rows('reference_2024')   # the variants derive from the 2024 base set
    base = run_clearing(None, None, horizon=24, reference_rows=(sup0, dem0), ntc_override=ntc0)
    sup, dem, ntc = scenario_rows('secheresse_hydro')
    assert sum(r['quantity'] for r in sup if r['profile'] == 'hydro') < sum(r['quantity'] for r in sup0 if r['profile'] == 'hydro') and ntc == ntc0
    dry = run_clearing(None, None, horizon=24, reference_rows=(sup, dem), ntc_override=ntc or None)
    assert dry['welfare'] < base['welfare'] and dry['summary']['reference_zones'] == C.ZONES
    sup, dem, ntc = scenario_rows('ligne_nga_ben')
    cut = run_clearing(None, None, horizon=24, reference_rows=(sup, dem), ntc_override=ntc)
    assert all(abs(v) == 0 for v in cut['flows']['NGA->BEN'].values()) and cut['welfare'] < base['welfare']
    sup, dem, ntc = scenario_rows('forte_demande', zones=['SEN'])
    q0 = scenario_rows('reference_2024', zones=['SEN'])[1][0]['quantity']
    assert {r['zone'] for r in sup} == {'SEN'} and dem[0]['quantity'] == round(q0 * 1.15)
    gas = [r for r in scenario_rows('gaz_cher')[0] if 'CCGT' in r['actor']]; gas0 = [r for r in sup0 if 'CCGT' in r['actor']]
    assert gas and all(g['price'] > g0['price'] for g, g0 in zip(gas, gas0))
    one = [dict(zone='SEN', player='x', actor='A', segment=0, quantity=10, price=10, profile='baseload')]
    r = run_clearing(one, [], horizon=1, fill_missing_zones=True, reference_rows=scenario_rows('gaz_cher')[:2])
    assert len(r['summary']['reference_zones']) == 13


def test_reference_2024_dataset_is_plausible():
    from engine.scenarios import scenario_rows, REFERENCE_2024, NTC_2024
    sup, dem, ntc = scenario_rows('reference_2024')
    assert set(REFERENCE_2024) == set(C.ZONES) and set(ntc) == set(C.NTC)
    total_sup = sum(r['quantity'] for r in sup); total_dem = sum(r['quantity'] for r in dem)
    assert 15000 < total_sup < 22000 and 13000 < total_dem < 20000
    assert all(C.P_MIN <= r['price'] <= C.P_MAX for r in sup + dem)
    res = run_clearing(None, None, horizon=24, reference_rows=(sup, dem), ntc_override=ntc)
    d = res['summary']['diagnostics']
    assert d['pro'] == 0 and d['pao'] == 0 and d['unsaturated_price_gaps'] == 0
    assert 0 < res['volume'] < 24 * total_sup
    # Togo offers units of a few tens of MW, no 100 MW default
    tgo = [r['quantity'] for r in sup if r['zone'] == 'TGO']
    assert max(tgo) <= 80


def test_fill_mode_actors_keeps_background_and_replaces_matching_actors():
    sup = [dict(zone='SEN', player='SENELEC', actor='Ma centrale', segment=0, quantity=50, price=90, profile='baseload')]
    dem = [dict(zone='SEN', player='SENELEC', actor='Ma charge', segment=0, quantity=300, price=200)]
    r = run_clearing(sup, dem, horizon=1, fill_mode='actors')
    actors = {(a['zone'], a['actor']) for a in r['summary']['actors']}
    assert ('SEN', 'OMVS Manantali') in actors          # background actor kept in the same zone
    assert ('SEN', 'SENELEC Thermal') not in actors and ('SEN', 'SENELEC Demand') not in actors   # replaced
    assert ('NGA', 'Egbin Gas') in actors                # other zones untouched
    assert r['summary']['n_supply'] == 64 - 3 + 1 and r['summary']['n_demand'] == 44 - 3 + 1
    # arbitrary name: nothing is replaced, the orders are added to the market
    r2 = run_clearing([dict(sup[0], player='Equipe 1')], [dict(dem[0], player='Equipe 1')], horizon=1, fill_mode='actors')
    assert r2['summary']['n_supply'] == 65 and r2['summary']['n_demand'] == 45
    # an order named after a reference actor replaces it
    r3 = run_clearing([dict(zone='NGA', player='Equipe 2', actor='Egbin Gas', segment=0, quantity=10, price=10, profile='baseload')], [], horizon=1, fill_mode='actors')
    assert ('NGA', 'Egbin Gas') in {(a['zone'], a['actor']) for a in r3['summary']['actors']}
    assert r3['summary']['n_supply'] == 64 - 4 + 1
    assert run_clearing(sup, dem, horizon=1, fill_mode='none')['summary']['n_supply'] == 1


#nouveau ajoutè par enrico
def test_mic_reinsertion():
    """AJOUTÉ : A et B ne couvrent pas leurs coûts au même tour et sont retirés ensemble. Une fois retirés,
    le prix monte à 40 : B, dont le taux de couverture était le plus élevé, est réinséré et couvre ses coûts ;
    A, réessayé ensuite, ferait retomber le prix et reste retiré."""
    sup = [dict(zone='NGA', player='a', actor='A', segment=0, quantity=50, price=10, profile='flat'),
           dict(zone='NGA', player='b', actor='B', segment=0, quantity=50, price=10, profile='flat'),
           dict(zone='NGA', player='c', actor='C', segment=0, quantity=100, price=40, profile='flat')]
    dem = [dict(zone='NGA', player='d', actor='L', segment=0, quantity=100, price=500)]
    mic = [dict(zone='NGA', player='a', actor='A', fixed_term=1000, variable_term=0),
           dict(zone='NGA', player='b', actor='B', fixed_term=900, variable_term=0)]
    res = run_clearing(sup, dem, hours=[12], ntc_override=NTC_ZERO, mic_rows=mic)
    st = {m['actor']: m for m in res['summary']['mic']}
    assert st['B']['satisfied'] and not st['B']['withdrawn']          # B réinséré
    assert st['A']['withdrawn']                                        # A reste retiré
    assert res['prices']['NGA']['12'] == 40.0
    assert res['summary']['diagnostics']['mic_withdrawn'] == ['A (NGA)']


    
#nouveau par ENRICO
def test_gas_scenario_raises_all_gas_plants():
    """AJOUTÉ : la variante « gaz cher » renchérit de 40 % chaque centrale de GAS_PLANTS_2024, et elles seules.
    Chaque nom de la liste doit exister dans le cas 2024 (protection contre une faute de frappe ou un renommage)."""
    from engine.scenarios import scenario_rows, REFERENCE_2024, GAS_PLANTS_2024
    names = {it[1] for items in REFERENCE_2024.values() for it in items if it[0] == 'S'}
    assert GAS_PLANTS_2024 <= names, GAS_PLANTS_2024 - names
    base, _, _ = scenario_rows('reference_2024')
    gas, _, _ = scenario_rows('gaz_cher')
    for r0, r1 in zip(base, gas):
        if r0['actor'] in GAS_PLANTS_2024:
            assert r1['price'] == min(C.P_MAX, round(r0['price'] * 1.4))
        else:
            assert r1['price'] == r0['price']


# pour le cas d'example de la section 2 du rapport
def test_two_zone_example_of_section_2():
    """AJOUTÉ : le moteur retrouve les solutions calculées à la main de l'exemple à deux zones du paper
    (section 2) : A = Nigeria, B = Bénin, ligne de 80 MW, heure 19 (profil de charge égal à 1)."""
    ntc = {k: 0.0 for k in C.NTC}; ntc[('NGA', 'BEN')] = 80.0
    def case(q_sb, p_d):
        sup = [dict(zone='NGA', player='x', actor='S_A', segment=0, quantity=100, price=20, profile='flat'),
               dict(zone='BEN', player='x', actor='S_B', segment=0, quantity=q_sb, price=50, profile='flat')]
        dem = [dict(zone='BEN', player='y', actor='D', segment=0, quantity=150, price=p_d)]
        r = run_clearing(sup, dem, hours=[19], ntc_override=ntc)
        acc = {g['actor']: g['accepted']['19'] for g in r['summary']['segments']}
        return r['welfare'], r['prices']['NGA']['19'], r['prices']['BEN']['19'], acc
    # Cas de base : W* = 9 900, y = (80, 70), prix 20 et 50
    W, pa, pb, acc = case(100, 100)
    assert W == 9900 and (acc['S_A'], acc['S_B']) == (80, 70) and (pa, pb) == (20, 50)
    # Cas dégénéré (q_SB = 70) : prix de B indéterminé dans [50, 100], P2 choisit le centre, 75
    W, pa, pb, acc = case(70, 100)
    assert W == 9900 and (pa, pb) == (20, 75)
    # Indétermination des volumes (prix de D = 50) : W* = 2 400, P1bis choisit le sommet (80, 70)
    W, pa, pb, acc = case(100, 50)
    assert W == 2400 and (acc['S_A'], acc['S_B']) == (80, 70) and (pa, pb) == (20, 50)