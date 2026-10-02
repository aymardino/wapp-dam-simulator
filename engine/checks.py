"""
Vérifications d'un résultat de clearing, indépendantes du solveur : équilibre, bornes, blocs liés et exclusifs,
MIC, cohérence des prix. Utilisées par les tests de propriétés et la campagne de simulations.
Retourne la liste des anomalies (vide si tout est cohérent).
"""
from .clearing import P_MIN, P_MAX, ZONES


def verify_result(res, tol=1.0):
    s = res['summary']
    hours = s['hours']
    problems = []
    d = s['diagnostics']
    if not d['pricing_feasible']:
        problems.append("prix : LP de prix infaisable")
    for k in ('pro', 'pao', 'unsaturated_price_gaps'):
        if d[k] != 0:
            problems.append(f"prix : {k} = {d[k]}")
    if abs(d['welfare_identity_gap']) > max(tol, 1e-6 * abs(s['welfare'])):
        problems.append(f"welfare : écart de l'identité {d['welfare_identity_gap']}")
    # Prix dans les bornes
    for z, series in res['prices'].items():
        for h, p in series.items():
            if not (P_MIN - 1e-6 <= p <= P_MAX + 1e-6):
                problems.append(f"prix {z} h{h} = {p} hors bornes")
    # Flux dans les NTC
    ntc = s['rules']['ntc']
    for k, series in res['flows'].items():
        cap = ntc[k]
        for h, f in series.items():
            if abs(f) > cap + 0.5:
                problems.append(f"flux {k} h{h} = {f} > NTC {cap}")
    # Équilibre global : somme des positions nettes nulle (pas de pertes)
    net = sum(zi['net_position'] for zi in s['zones'].values())
    if abs(net) > tol * len(ZONES):
        problems.append(f"équilibre : somme des positions nettes = {net}")
    # Demande acceptée = production acceptée à chaque heure
    disp = res['dispatch']
    for i, h in enumerate(hours):
        gen = sum(disp[k][i] for k in disp if k != 'demand')
        if abs(gen - disp['demand'][i]) > tol:
            problems.append(f"équilibre h{h} : production {gen:.1f} ≠ demande {disp['demand'][i]:.1f}")
    # Acteurs : accepté ≤ offert
    for a in s['actors']:
        if a['accepted_mwh'] > a['offered_mwh'] + tol:
            problems.append(f"acteur {a['actor']} ({a['zone']}) : accepté {a['accepted_mwh']} > offert {a['offered_mwh']}")
    # Blocs : pas de PAB, enfants ⇒ parents, groupes exclusifs ≤ 1
    blocks = s['blocks']
    by_name = {(b['zone'], b.get('player'), b['name']): b for b in blocks}
    groups = {}
    for b in blocks:
        if b['status'] == 'PAB' and s['rules']['pab_rule'] != 'none':
            problems.append(f"bloc {b['name']} : PAB non corrigé")
        if b['accepted'] and b.get('parent'):
            parent = by_name.get((b['zone'], b.get('player'), b['parent']))
            if parent is not None and not parent['accepted']:
                problems.append(f"bloc {b['name']} accepté sans son parent {b['parent']}")
        if b.get('group'):
            groups.setdefault((b['zone'], b.get('player'), b['group']), []).append(b['accepted'])
    for g, acc in groups.items():
        if sum(acc) > 1:
            problems.append(f"groupe exclusif {g} : {sum(acc)} options acceptées")
    # MIC : chaque condition est satisfaite ou retirée
    for m in s['mic']:
        if not (m['satisfied'] or m['withdrawn']):
            problems.append(f"MIC {m['actor']} ({m['zone']}) ni satisfaite ni retirée")
    return problems
