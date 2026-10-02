"""
Solver-independent checks of a clearing result: balance, bounds, linked and exclusive blocks,
MIC, price consistency. Used by the property tests and the simulation campaign.
Returns the list of anomalies (empty when everything is consistent).
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
        problems.append(f"welfare: identity gap {d['welfare_identity_gap']}")
    # Prices within bounds
    for z, series in res['prices'].items():
        for h, p in series.items():
            if not (P_MIN - 1e-6 <= p <= P_MAX + 1e-6):
                problems.append(f"prix {z} h{h} = {p} hors bornes")
    # Flows within NTC
    ntc = s['rules']['ntc']
    for k, series in res['flows'].items():
        cap = ntc[k]
        for h, f in series.items():
            if abs(f) > cap + 0.5:
                problems.append(f"flux {k} h{h} = {f} > NTC {cap}")
    # Global balance: net positions sum to zero (no losses)
    net = sum(zi['net_position'] for zi in s['zones'].values())
    if abs(net) > tol * len(ZONES):
        problems.append(f"balance: sum of net positions = {net}")
    # Accepted demand = accepted generation at every hour
    disp = res['dispatch']
    for i, h in enumerate(hours):
        gen = sum(disp[k][i] for k in disp if k != 'demand')
        if abs(gen - disp['demand'][i]) > tol:
            problems.append(f"balance h{h}: generation {gen:.1f} ≠ demand {disp['demand'][i]:.1f}")
    # Actors: accepted ≤ offered
    for a in s['actors']:
        if a['accepted_mwh'] > a['offered_mwh'] + tol:
            problems.append(f"actor {a['actor']} ({a['zone']}): accepted {a['accepted_mwh']} > offered {a['offered_mwh']}")
    # Blocks: no PAB, children ⇒ parents, exclusive groups ≤ 1
    blocks = s['blocks']
    by_name = {(b['zone'], b.get('player'), b['name']): b for b in blocks}
    groups = {}
    for b in blocks:
        if b['status'] == 'PAB' and s['rules']['pab_rule'] != 'none':
            problems.append(f"block {b['name']}: uncorrected PAB")
        if b['accepted'] and b.get('parent'):
            parent = by_name.get((b['zone'], b.get('player'), b['parent']))
            if parent is not None and not parent['accepted']:
                problems.append(f"block {b['name']} accepted without its parent {b['parent']}")
        if b.get('group'):
            groups.setdefault((b['zone'], b.get('player'), b['group']), []).append(b['accepted'])
    for g, acc in groups.items():
        if sum(acc) > 1:
            problems.append(f"exclusive group {g}: {sum(acc)} options accepted")
    # MIC: every condition is satisfied or withdrawn
    for m in s['mic']:
        if not (m['satisfied'] or m['withdrawn']):
            problems.append(f"MIC {m['actor']} ({m['zone']}) neither satisfied nor withdrawn")
    return problems
