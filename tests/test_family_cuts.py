"""Coupes de famille sur les blocs paradoxalement acceptés (Section 2.7.1 du paper).

Cas à une zone (GIN) et quatre heures, avec une famille : un parent P et deux enfants C0 et C1.
À la première itération, P1 accepte la famille entière, mais C0 et C1 sont alors paradoxalement
acceptés. L'ancienne règle fixait C0 et C1 à « rejeté » pour toujours : il ne restait que le parent
seul. Avec les coupes de famille, seule la configuration {P, C0, C1} est exclue, et P1 retient
ensuite P avec C0, sans aucun PAB et avec un bien-être plus élevé.
"""
from engine.clearing import run_clearing

HOURS = [0, 1, 2, 3]

SUPPLY = [
    dict(zone='GIN', player='p', actor='S0', segment=0, quantity=80, price=10, profile='baseload'),
    dict(zone='GIN', player='p', actor='S1', segment=0, quantity=50, price=20, profile='baseload'),
    dict(zone='GIN', player='p', actor='S2', segment=0, quantity=80, price=10, profile='baseload'),
]
DEMAND = [
    dict(zone='GIN', player='c', actor='D', segment=0, quantity=50, price=200),
]
BLOCKS = [
    dict(name='P', zone='GIN', side='D', quantity=100, price=50, h_start=1, h_end=2, player='s'),
    dict(name='C0', zone='GIN', side='D', quantity=50, price=80, h_start=0, h_end=1, player='s',
         parent_name='P'),
    dict(name='C1', zone='GIN', side='D', quantity=50, price=80, h_start=1, h_end=2, player='s',
         parent_name='P'),
]


def _clear(**kw):
    """Clearing du cas test, sans acteurs de référence."""
    return run_clearing(SUPPLY, DEMAND, hours=HOURS, block_rows=BLOCKS, fill_mode='none', **kw)['summary']


def test_family_cut_keeps_parent_with_one_child():
    """La configuration paradoxale est exclue, mais P1 peut encore accepter le parent avec un enfant."""
    s = _clear()
    status = {b['name']: b['accepted'] for b in s['blocks']}
    assert status == {'P': True, 'C0': True, 'C1': False}
    # Aucun bloc accepté à perte dans le résultat publié.
    assert s['diagnostics']['pab'] == []


def test_family_cut_excludes_only_the_paradoxical_configuration():
    """La coupe porte sur la configuration {P, C0, C1}, et aucun bloc n'est fixé à « rejeté »."""
    s = _clear()
    notes = [n for n in s['diagnostics']['notes'] if 'family configuration excluded' in n]
    assert len(notes) == 1
    assert "'P': 1" in notes[0] and "'C0': 1" in notes[0] and "'C1': 1" in notes[0]
    assert s['diagnostics']['blocks_fixed'] == {}


def test_accepted_family_is_not_paradoxical():
    """Le surplus de la famille acceptée, aux prix publiés, n'est pas une perte."""
    s = _clear()
    fam = sum(b['surplus'] for b in s['blocks'] if b['accepted'])
    assert fam >= 0
