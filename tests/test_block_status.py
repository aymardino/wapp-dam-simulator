"""
Statut PRB des blocs liés et des groupes exclusifs (Section 2.7.1 de l'article).

Un bloc rejeté n'est paradoxalement rejeté (PRB) que si son propriétaire aurait préféré une issue
que les liens entre ses blocs permettaient : une famille dont le parent est rejeté est jugée en
entier, et dans un groupe exclusif un bloc rejeté n'est PRB que s'il valait mieux que le bloc
accepté, ou, sans bloc accepté, s'il est le meilleur du groupe.
Les premiers tests appellent directement _price_blocks avec des prix fixés, pour que le résultat
attendu se calcule à la main ; le dernier vérifie le scénario d'ordres complexes R5 de l'article.
"""
from engine.clearing import Block, _price_blocks, run_clearing
from engine.scenarios import scenario_rows, complex_orders_rows

H = [0, 1]                       # deux heures
PRIX = {('SEN', 0): 100.0, ('SEN', 1): 100.0}


def bloc(nom, prix, q=10, cote='D', parent=None, groupe=None):
    """Bloc d'achat (par défaut) sur les deux heures, dans la zone SEN.
    Surplus d'un achat aux prix PRIX : (prix - 100) × q × 2."""
    return Block(name=nom, zone='SEN', side=cote, q=q, p=prix, hours=H, parent=parent, group=groupe,
                 player='T', active_hours=H)


def statuts(blocs, acceptes, parent_of=None, groupes=None):
    y = {i: int(b.name in acceptes) for i, b in enumerate(blocs)}
    res = _price_blocks(blocs, y, PRIX, parent_of or {}, groupes or [])
    return {r['name']: (r['status'], r['prb_basis']) for r in res}


def test_groupe_bloc_accepte_meilleur():
    # A rapporte 400, B (accepté) 1 000 : le propriétaire préfère B, A n'est pas paradoxal
    blocs = [bloc('A', 120, groupe='g'), bloc('B', 150, groupe='g')]
    st = statuts(blocs, {'B'}, groupes=[[0, 1]])
    assert st['A'] == ('OK', 'group')


def test_groupe_bloc_rejete_meilleur():
    # A (rejeté) rapporte 1 000, B (accepté) 400 : A aurait été préféré, il est PRB
    blocs = [bloc('A', 150, groupe='g'), bloc('B', 120, groupe='g')]
    st = statuts(blocs, {'B'}, groupes=[[0, 1]])
    assert st['A'] == ('PRB', 'group')


def test_groupe_sans_bloc_accepte():
    # Aucun bloc accepté : seul le meilleur (B, 1 000 contre 400) peut être PRB
    blocs = [bloc('A', 120, groupe='g'), bloc('B', 150, groupe='g')]
    st = statuts(blocs, set(), groupes=[[0, 1]])
    assert st['A'] == ('OK', 'group') and st['B'] == ('PRB', 'group')


def test_famille_rejetee_gagnante():
    # Parent P : -200 ; enfant C1 : +600 ; enfant C2 : -100. Famille sans C2 : +400 > 0,5 × 40 MWh :
    # P et C1 sont PRB au titre de la famille, C2 (en perte) ne l'est pas
    blocs = [bloc('P', 90), bloc('C1', 130, parent='P'), bloc('C2', 95, parent='P')]
    st = statuts(blocs, set(), parent_of={1: 0, 2: 0})
    assert st['P'] == ('PRB', 'family') and st['C1'] == ('PRB', 'family') and st['C2'] == ('OK', 'family')


def test_famille_rejetee_perdante():
    # Parent P : -800 ; enfant C : +600. L'enfant gagnerait seul, mais il ne pouvait pas être accepté
    # sans son parent, et la famille perd 200 : aucun bloc n'est paradoxal
    blocs = [bloc('P', 60), bloc('C', 130, parent='P')]
    st = statuts(blocs, set(), parent_of={1: 0})
    assert st['P'] == ('OK', 'family') and st['C'] == ('OK', 'family')


def test_enfant_rejete_parent_accepte():
    # Parent accepté : l'enfant rejeté pouvait être accepté, il est jugé seul (+600, PRB)
    blocs = [bloc('P', 110), bloc('C', 130, parent='P')]
    st = statuts(blocs, {'P'}, parent_of={1: 0})
    assert st['P'] == ('OK', 'block') and st['C'] == ('PRB', 'block')


def test_bloc_seul_inchange():
    # Bloc sans lien : règle (20) inchangée, PRB au-delà de 0,5 USD/MWh, OK en dessous
    assert statuts([bloc('X', 130)], set())['X'] == ('PRB', 'block')
    assert statuts([bloc('Y', 100.3)], set())['Y'] == ('OK', 'block')


def test_scenario_r5():
    """Scénario R5 : Desalination A n'est plus PRB (B, accepté, rapporte plus) ; la famille de la
    fonderie est PRB au titre de la famille ; le bien-être et les décisions ne changent pas."""
    sup, dem, ntc = scenario_rows('reference_2024')
    blocks, mic = complex_orders_rows()
    res = run_clearing(sup, dem, ntc_override=ntc, block_rows=blocks, mic_rows=mic)
    st = {b['name']: (b['accepted'], b['status'], b['prb_basis']) for b in res['summary']['blocks']}
    assert st['Desalination A (all day)'] == (False, 'OK', 'group')
    assert st['Desalination B (night)'][:2] == (True, 'OK')
    assert st['Desalination C (day)'] == (False, 'OK', 'group')
    for n in ('Smelter potline 1', 'Smelter potline 2', 'Smelter potline 3 (night)'):
        assert st[n] == (False, 'PRB', 'family'), n
