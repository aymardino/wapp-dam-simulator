"""
Solver-independent checks of a clearing result: balance, bounds, linked and exclusive blocks,
MIC, price consistency. Used by the property tests and the simulation campaign.
Returns the list of anomalies (empty when everything is consistent).
"""
from .clearing import P_MIN, P_MAX, ZONES, X_TOL, F_TOL, PRICE_TOL, ALPHA, ALPHA_LINES  #modifie par enrico


def verify_result(res, tol=1.0):
    s = res['summary']
    hours = s['hours']
    problems = []
    d = s['diagnostics']
    if not d['pricing_feasible']:
        problems.append("prix : LP de prix infaisable")
    #modifcation ENRICO    # Prix : contrôle recalculé ici, sans utiliser les compteurs du moteur, à partir des prix publiés et
    # du détail de chaque segment (summary['segments']) ; il doit donner zéro avec la règle complète.
    problems += _check_prices(res)
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
    #nouvea par ENRICO# Bilan de chaque zone sur la journée : position nette = flux sortants - flux entrants
    for z, zi in s['zones'].items():
        exports, n_lines = 0.0, 0
        for k, series in res['flows'].items():
            u, v = k.split('->')
            if z in (u, v):
                exports += sum(series.values()) * (1 if u == z else -1)
                n_lines += 1
     #nouveau   # marge : arrondi des flux publiés (0,05 MW par ligne et par heure)
        if abs(zi['net_position'] - exports) > tol + 0.05 * len(hours) * n_lines:
            problems.append(f"balance {z}: net position {zi['net_position']} ≠ net exports {exports:.1f}")
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



#nouvelle par ENRICO
def _check_prices(res):
    """Conditions de marché recalculées à partir des prix publiés : ordres paradoxalement rejetés ou
    acceptés, ordres partiels dont le prix n'est pas le prix de la zone, écarts de prix sur les lignes
    non saturées (sauf les lignes du Burkina Faso quand la contrainte α est active)."""
    s = res['summary']
    prices, flows, ntc = res['prices'], res['flows'], s['rules']['ntc']
    out, pro, pao, part, gaps = [], 0, 0, 0, 0
    for g in s.get('segments', []):
        for h, q in g['offered'].items():
            x = g['accepted'][h] / q
            P = prices[g['zone']][h]
            sign = 1 if g['side'] == 'S' else -1          # vente : gagne si P > prix ; achat : si P < prix
            gain = sign * (P - g['price'])
            if x < X_TOL and gain > PRICE_TOL:
                pro += 1                                   # rejeté alors qu'il aurait gagné
            elif x > 1 - X_TOL and gain < -PRICE_TOL:
                pao += 1                                   # accepté alors qu'il perd
            elif X_TOL <= x <= 1 - X_TOL and abs(gain) > PRICE_TOL:
                part += 1                                  # partiel, mais le prix n'est pas le sien
    # Les flux publiés sont arrondis à 0,1 MW : marge de 0,1 MW pour décider de la saturation
    marge = 0.1 + F_TOL
    alpha_lines = {f"{u}->{v}" for u, v in ALPHA_LINES}
    hours = s['hours']
    alpha_cap = ALPHA * sum(ntc[k] for k in alpha_lines if k in ntc)
    for k, series in flows.items():
        u, v = k.split('->')
        for h, f in series.items():
            if abs(f) >= ntc[k] - marge:
                continue                                   # ligne saturée : écart de prix permis
            if k in alpha_lines and sum(flows[a][h] for a in alpha_lines if a in flows) >= alpha_cap - marge:
                continue                                   # contrainte α active : écart permis
            if abs(prices[u][h] - prices[v][h]) > PRICE_TOL:
                gaps += 1
    for name, n in (('pro', pro), ('pao', pao), ('partial_off_price', part), ('unsaturated_price_gaps', gaps)):
        if n:
            out.append(f"prix : {name} = {n} (contrôle indépendant)")
    return out