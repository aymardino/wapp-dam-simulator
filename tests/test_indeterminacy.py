"""
Indétermination résiduelle des prix et règle P2 quadratique.

Une région de prix (zones reliées par des lignes non saturées) qui ne contient aucun ordre
partiellement accepté a un prix indéterminé : P2 le choisit. Avec l'objectif L1, ce choix
n'était pas toujours unique dans une région de plusieurs zones ; avec la somme des écarts
au carré (Section 2.7 de l'article), il l'est. Ces tests
  1. comptent et affichent ces régions (diagnostic, sans échec) ;
  2. vérifient que P2 a été résolu avec l'objectif quadratique et que P1bis n'a pas eu besoin
     de son repli (tie_break 'exact'), dans tous les scénarios et dans R5 ;
  3. vérifient le cas trouvé dans le cas de référence : région CIV–GIN–LBR–SLE à l'heure 7 ;
  4. vérifient que, sans solveur quadratique, le clearing s'arrête avec un message d'installation.
"""
import pytest

import engine.clearing as C
from engine.clearing import run_clearing, ClearingError, P_MIN, P_MAX
from engine.scenarios import scenario_rows, complex_orders_rows

# Tolérances de lecture du résultat (Section 2.4.2 de l'article)
EPS_X = 1e-4   # rapport d'acceptation : accepté / partiel / rejeté
EPS_F = 1e-3   # MW : une ligne est saturée si |f| >= NTC - EPS_F
EPS_W = 1e-6   # USD/MWh : largeur minimale d'un intervalle indéterminé

SCENARIOS = ['reference_2024', 'secheresse_hydro', 'ligne_nga_ben', 'gaz_cher', 'forte_demande']


def _val(serie, h):
    """Lit une valeur horaire, que les heures soient des entiers ou des chaînes."""
    return serie.get(str(h), serie.get(h, 0.0))


def _clearing(nom):
    """Clearing d'un scénario de scenario_rows, ou du scénario R5 (même construction que r5())."""
    if nom != 'ordres_complexes_r5':
        sup, dem, ntc = scenario_rows(nom)
        return run_clearing(sup, dem, ntc_override=ntc)
    sup, dem, ntc = scenario_rows('reference_2024')
    blocks, mic = complex_orders_rows()
    return run_clearing(sup, dem, ntc_override=ntc, block_rows=blocks, mic_rows=mic)


def _regions(res, h):
    """Regroupe les zones reliées par des lignes non saturées (union-find)."""
    lignes = res['summary']['lines']
    zones = list(res['prices'].keys())
    parent = {z: z for z in zones}

    def racine(z):
        while parent[z] != z:
            parent[z] = parent[parent[z]]
            z = parent[z]
        return z

    # Contrainte conjointe du Burkina Faso, équation (21) : est-elle active à cette heure ?
    lignes_alpha = {f"{u}->{v}" for u, v in C.ALPHA_LINES}
    import_conjoint = sum(_val(res['flows'][k], h) for k in lignes_alpha)
    limite = C.ALPHA * sum(lignes[k]['ntc'] for k in lignes_alpha)
    conjointe_active = import_conjoint >= limite - EPS_F

    for k in lignes:
        o, d = k.split('->')
        saturee = abs(_val(res['flows'][k], h)) >= lignes[k]['ntc'] - EPS_F
        # Si (21) est active, νh peut séparer les prix sans saturation : on ne fusionne pas
        if saturee or (k in lignes_alpha and conjointe_active):
            continue
        parent[racine(o)] = racine(d)

    groupes = {}
    for z in zones:
        groupes.setdefault(racine(z), []).append(z)
    return list(groupes.values())


def _sans_ordre_marginal(res):
    """Régions-heures de plusieurs zones sans ordre partiel et d'intervalle (13) non réduit à un point."""
    s = res['summary']
    retires = {(m['zone'], m['actor']) for m in s.get('mic', []) if m['withdrawn']}
    regions_total, mono, multi = 0, 0, []
    for h in s['hours']:
        for region in _regions(res, h):
            regions_total += 1
            bas, haut, marginal = P_MIN, P_MAX, False
            for sg in s['segments']:
                if sg['zone'] not in region or (sg['zone'], sg.get('actor')) in retires:
                    continue      # hors région, ou acteur retiré par sa condition de revenu minimum
                q = _val(sg['offered'], h)
                if q <= 0:
                    continue      # segment sans quantité à cette heure (solaire la nuit)
                r = _val(sg['accepted'], h) / q
                if EPS_X < r < 1 - EPS_X:
                    marginal = True
                accepte = r > EPS_X
                if (sg['side'] == 'S') == accepte:
                    bas = max(bas, sg['price'])     # vendeur accepté ou acheteur rejeté
                else:
                    haut = min(haut, sg['price'])   # vendeur rejeté ou acheteur accepté
            if marginal or haut - bas <= EPS_W:
                continue
            if len(region) == 1:
                mono += 1
            else:
                multi.append((h, sorted(region), round(bas, 2), round(haut, 2)))
    return regions_total, mono, multi


@pytest.mark.parametrize('nom', SCENARIOS + ['ordres_complexes_r5'])
def test_p2_quadratique(nom):
    res = _clearing(nom)
    total, mono, multi = _sans_ordre_marginal(res)
    print(f"\n{nom}: {total} régions-heures, {mono} sans ordre marginal à une zone, "
          f"{len(multi)} à plusieurs zones {multi}")
    diag = res['summary']['diagnostics']
    # Le prix de ces régions n'est unique que si P2 a été résolu avec l'objectif quadratique
    assert diag['pricing_objective'] == 'quadratic', nom
    # P1bis a trouvé le dispatch de volume maximal sans recourir à la solution de P1 (Section 2.7)
    assert diag['tie_break'] == 'exact', nom


def test_region_ouest_heure_7():
    """Cas de référence, heure 7 : la région CIV–GIN–LBR–SLE n'a pas d'ordre marginal.
    Références 86, 77,5, 70 et 67,5 ; prix admissibles [62, 72] (ligne CIV→GHA saturée,
    prix du Ghana fixé à 72 par Sunon Asogli). L'objectif L1 est plat sur [70, 72] ;
    le quadratique donne la moyenne 75,25 ramenée dans l'intervalle, soit 72, de façon unique."""
    res = _clearing('reference_2024')
    _, _, multi = _sans_ordre_marginal(res)
    assert any(h in (7, '7') and r == ['CIV', 'GIN', 'LBR', 'SLE'] for h, r, _, _ in multi)
    for z in ('CIV', 'GIN', 'LBR', 'SLE'):
        assert abs(_val(res['prices'][z], 7) - 72.0) < 1e-4, z


def test_solveur_quadratique_disponible():
    """P2 a besoin d'un solveur quadratique (Gurobi ou l'interface Pyomo 'highs')."""
    assert hasattr(C, '_get_qp_solver'), "clearing.py sans P2 quadratique (_get_qp_solver absent)"
    solveur, nom = C._get_qp_solver()
    assert solveur is not None, "aucun solveur quadratique : installer highspy et une version récente de Pyomo"


def test_sans_solveur_quadratique_erreur(monkeypatch):
    """Sans solveur quadratique, la règle 'complete' s'arrête avec un message d'installation au lieu
    de publier des prix calculés avec une autre règle ; la règle 'l2' (comparaison) n'en a pas besoin."""
    monkeypatch.setattr(C, '_get_qp_solver', lambda: (None, None))
    sup, dem, ntc = scenario_rows('reference_2024')
    with pytest.raises(ClearingError, match='pip install'):
        run_clearing(sup, dem, ntc_override=ntc)
    res = run_clearing(sup, dem, ntc_override=ntc, pricing='l2')
    assert res['summary']['diagnostics']['pricing_objective'] == 'absolute'
