"""
Résultats du paper : calcule les analyses R1 à R4 sur le cas de référence 2024 et écrit les tableaux LaTeX
et les figures dans le dossier results/.

À lancer depuis la racine du dépôt :
    python scripts/results.py            (toutes les analyses disponibles)
    python scripts/results.py r1         (une seule analyse)

Chaque analyse est une fonction r1(), r2()… indépendante ; les calculs passent tous par run_clearing.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import matplotlib
matplotlib.use('Agg')                                   # pas d'affichage : on écrit seulement des fichiers
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

from engine.scenarios import scenario_rows, actor_name_en, complex_orders_rows, COMPLEX_ORDERS_BLOCKS, COMPLEX_ORDERS_MIC
from engine.clearing import run_clearing, ZONES, F_TOL

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
os.makedirs(OUT, exist_ok=True)

NAMES = {'NGA': 'Nigeria', 'GHA': 'Ghana', 'CIV': "Côte d'Ivoire", 'SEN': 'Senegal', 'BFA': 'Burkina Faso',
         'MLI': 'Mali', 'NER': 'Niger', 'BEN': 'Benin', 'TGO': 'Togo', 'GIN': 'Guinea', 'SLE': 'Sierra Leone',
         'LBR': 'Liberia', 'GMB': 'The Gambia', 'GNB': 'Guinea-Bissau'}

# Position schématique de chaque zone sur la carte (longitude, latitude approximatives des centres de réseau)
POS = {'SEN': (-13.6, 15.2), 'GMB': (-17.0, 13.5), 'GNB': (-16.2, 11.3), 'GIN': (-12.0, 9.9), 'SLE': (-13.4, 7.6),
       'LBR': (-9.8, 6.3), 'CIV': (-5.4, 7.0), 'MLI': (-7.4, 12.8), 'BFA': (-1.6, 12.2), 'GHA': (-1.0, 7.0),
       'TGO': (1.6, 8.3), 'BEN': (3.6, 9.4), 'NER': (2.6, 13.6), 'NGA': (7.0, 9.3)}
# Position du nom de chaque zone par rapport à son cercle : 'below' (dessous) ou 'above' (dessus)
LABEL = {z: 'below' for z in POS}
LABEL.update({'SEN': 'above', 'GMB': 'above', 'MLI': 'above', 'BFA': 'above', 'NER': 'above', 'GIN': 'above'})


def fmt(x, d=0):
    """Nombre au format LaTeX : séparateur de milliers {,} et signe moins typographique."""
    s = f"{abs(x):,.{d}f}".replace(',', '{,}')
    return ('$-$' if x < 0 else '') + s


def write(name, text):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        f.write(text)
    print('  écrit', name)


def run(key='reference_2024', **kw):
    """Lance le clearing d'un scénario avec ses capacités explicites (indépendant de la base du site web)."""
    sup, dem, ntc = scenario_rows(key)
    ntc = kw.pop('ntc', ntc)
    return run_clearing(sup, dem, ntc_override=ntc, **kw)


# ── Carte des prix et des flux ─────────────────────────────────────────────────────────────────────
# Frontières : Natural Earth 1:50m (domaine public), découpées sur l'Afrique de l'Ouest dans scripts/data/.
# Positions des zones : centres approximatifs des réseaux nationaux (longitude, latitude).
GEO = {'SEN': (-14.6, 14.5), 'GMB': (-16.9, 13.6), 'GNB': (-15.4, 11.5), 'GIN': (-11.2, 11.0), 'SLE': (-12.0, 8.6),
       'LBR': (-9.9, 6.4), 'CIV': (-5.3, 6.9), 'MLI': (-6.6, 14.2), 'BFA': (-1.5, 12.2), 'GHA': (-1.1, 7.2),
       'TGO': (1.4, 6.6), 'BEN': (3.4, 7.0), 'NER': (5.0, 13.4), 'NGA': (7.6, 8.4)}
WAPP_ISO = set(ZONES)


def _borders():
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'west_africa.geojson')
    with open(path, encoding='utf-8') as f:
        return json.load(f)['features']


def draw_hourly(res, filename):
    """Prix de chaque zone heure par heure, valeurs écrites dans les cases. Les zones sont réunies en groupes
    de prix (même prix au moins 75 % des heures), séparés par un trait blanc et triés par prix moyen pondéré."""
    from matplotlib.colors import LinearSegmentedColormap
    plt.rcParams['font.family'] = 'serif'
    prices, zones = res['prices'], res['summary']['zones']
    hours = [str(h) for h in res['summary']['hours']]
    # Groupes de prix : deux zones sont dans le même groupe si leurs prix sont égaux au moins 75 % des heures
    def similar(a, b):
        return sum(abs(prices[a][h] - prices[b][h]) < 0.5 for h in hours) / len(hours) >= 0.75
    groups = []
    for z in sorted(ZONES, key=lambda z: -zones[z]['avg_price']):
        g = next((g for g in groups if any(similar(z, y) for y in g)), None)
        if g is None:
            groups.append([z])
        else:
            g.append(z)
    groups.sort(key=lambda g: -sum(zones[z]['avg_price'] for z in g) / len(g))
    order = [z for g in groups for z in g]
    breaks = [sum(len(g) for g in groups[:k]) for k in range(1, len(groups))]
    data = [[prices[z][h] for h in hours] for z in order]
    cmap = LinearSegmentedColormap.from_list('price', ['#e8f1ee', '#f3d77a', '#e3955a', '#b03a3a'])

    fig, ax = plt.subplots(figsize=(13, 5.6))
    im = ax.imshow(data, aspect='auto', cmap=cmap, interpolation='nearest')
    for i, row in enumerate(data):
        for j, v in enumerate(row):
            ax.text(j, i, f"{v:.0f}", ha='center', va='center', fontsize=8,
                    color='white' if im.norm(v) > 0.8 else '#1a1a1a')
    # Traits blancs entre les groupes de prix
    for i in breaks:
        ax.axhline(i - 0.5, color='white', lw=5)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([f"{z}  ({zones[z]['avg_price']:.0f})" for z in order], fontsize=11)
    ax.set_xticks(range(len(hours)))
    ax.set_xticklabels([f"{int(h):02d}" for h in hours], fontsize=11)
    ax.set_xlabel('hour of delivery', fontsize=12)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(im, ax=ax, pad=0.01, fraction=0.03)
    cb.set_label('$/MWh')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, filename), dpi=200, bbox_inches='tight')
    plt.close(fig)
    plt.rcParams['font.family'] = 'sans-serif'
    print('  écrit', filename)


def draw_map(res, h, filename, title=None):
    """Carte des prix de zone et des flux à l'heure h : cercles colorés par le prix, lignes vertes dont
    l'épaisseur est la part de la capacité utilisée, lignes saturées en rouge, flèches dans le sens du flux."""
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import Polygon
    from matplotlib.lines import Line2D
    plt.rcParams['font.family'] = 'serif'
    prices, flows, lines = res['prices'], res['flows'], res['summary']['lines']
    cmap = LinearSegmentedColormap.from_list('price', ['#e8f1ee', '#f3d77a', '#e3955a', '#b03a3a'])
    norm = Normalize(vmin=min(prices[z][h] for z in ZONES), vmax=max(prices[z][h] for z in ZONES))
    GREEN, RED = '#1b7a5e', '#b03a3a'

    fig, ax = plt.subplots(figsize=(12, 5.9))
    ax.set_facecolor('#e3ebf1')                                   # la mer
    for f in _borders():
        fc = '#f7f5f0' if f['properties']['iso'] in WAPP_ISO else '#e8e4dc'
        for poly in f['geometry']['coordinates']:
            ax.add_patch(Polygon(poly[0], closed=True, fc=fc, ec='#6b6b6b', lw=0.6, zorder=0))

    for k, l in lines.items():
        u, v = k.split('->')
        f = flows[k][h]
        (x0, y0), (x1, y1) = GEO[u], GEO[v]
        cap = l['ntc']
        sat = cap > 0 and abs(f) >= cap - 0.1 - F_TOL
        share = min(1.0, abs(f) / cap) if cap else 0.0
        ax.plot([x0, x1], [y0, y1], color=RED if sat else GREEN, lw=2 + 6 * share, alpha=0.9,
                solid_capstyle='butt', zorder=2)
        if abs(f) > 1:
            a, b = ((x0, y0), (x1, y1)) if f > 0 else ((x1, y1), (x0, y0))
            mx, my = a[0] + 0.55 * (b[0] - a[0]), a[1] + 0.55 * (b[1] - a[1])
            import math
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))      # sens du flux (axes de même échelle)
            ax.plot(mx, my, marker=(3, 0, ang - 90), ms=9, color='#5c1a1a' if sat else '#0b3d2e', zorder=3)

    for z in ZONES:
        x, y = GEO[z]
        c = cmap(norm(prices[z][h]))
        ax.scatter(x, y, s=1050, color=c, edgecolor='white', linewidth=2, zorder=4)
        dark = norm(prices[z][h]) > 0.75
        ax.text(x, y + 0.28, z, fontsize=10, fontweight='bold', ha='center', va='center',
                color='white' if dark else '#1a1a1a', zorder=5)
        ax.text(x, y - 0.35, f"{prices[z][h]:.0f}", fontsize=10, ha='center', va='center',
                color='white' if dark else '#1a1a1a', zorder=5)

    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, ax=ax, pad=0.01, fraction=0.03, shrink=0.85)
    cb.set_label('zonal price, $/MWh')
    ax.legend(handles=[Line2D([0], [0], color=GREEN, lw=4, label='flow (width: share of capacity used)'),
                       Line2D([0], [0], color=RED, lw=4, label='saturated line')],
              loc='upper left', fontsize=10, framealpha=0.95)
    ax.set_xlim(-18.0, 16.5); ax.set_ylim(3.6, 20.0)
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    if title:
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, filename), dpi=200, bbox_inches='tight')
    plt.close(fig)
    plt.rcParams['font.family'] = 'sans-serif'
    print('  écrit', filename)


# ══════════════════════════════════════════════════════════════════════════════════════════════════
# R1 — Le marché 2024 : prix, positions nettes, lignes saturées
# ══════════════════════════════════════════════════════════════════════════════════════════════════
def r1():
    print('R1 — cas de référence 2024')
    res = run()
    s = res['summary']
    hours = s['hours']
    prices, flows = res['prices'], res['flows']
    zones, lines = s['zones'], s['lines']

    # ── Tableau R1-a : indicateurs agrégés ──
    n_sat = sum(1 for l in lines.values() if l['saturated_hours'] > 0)
    write('tab_r1_aggregate.tex', rf"""\begin{{table}}[!htbp]
\centering
\small
\caption{{Reference case 2024: aggregate results for one day.}}\label{{tab:r1-aggregate}}
\begin{{tabular}}{{@{{}}lr@{{}}}}
\toprule
Indicator & Value \\
\midrule
Traded volume (MWh) & {fmt(s['volume'])} \\
Consumer surplus (M\$) & {s['consumer_surplus']/1e6:.2f} \\
Producer surplus (M\$) & {s['producer_surplus']/1e6:.2f} \\
Congestion rent (M\$) & {s['congestion_rent']/1e6:.2f} \\
Lines saturated at least one hour & {n_sat} of {len(lines)} \\
\bottomrule
\end{{tabular}}
\end{{table}}
""")

    # ── Tableau R1-b : chaque zone ──
    order = sorted(ZONES, key=lambda z: -zones[z]['avg_price'])
    rows = '\n'.join(
        f"{NAMES[z]} & {zones[z]['avg_price']:.0f} & {fmt(zones[z]['generation_mwh'])} & {fmt(zones[z]['load_mwh'])} "
        f"& {fmt(zones[z]['net_position'])} \\\\" for z in order)
    write('tab_r1_zones.tex', rf"""\begin{{table}}[!htbp]
\centering
\small
\caption{{Reference case 2024: average price weighted by consumption (USD/MWh), generation, consumption and net position (MWh per day, exports positive) of each zone.}}\label{{tab:r1-zones}}
\begin{{tabular}}{{@{{}}lrrrr@{{}}}}
\toprule
Zone & Price & Generation & Consumption & Net position \\
\midrule
{rows}
\bottomrule
\end{{tabular}}
\end{{table}}
""")

    # ── Tableau R1-c : chaque ligne ──
    def gap(k):
        u, v = k.split('->')
        return sum(abs(prices[v][h] - prices[u][h]) for h in prices[u]) / len(hours)
    lorder = sorted(lines, key=lambda k: (-lines[k]['saturated_hours'], -lines[k]['congestion_rent']))
    rows = '\n'.join(
        f"{NAMES[k.split('->')[0]]}--{NAMES[k.split('->')[1]]} & {lines[k]['ntc']:.0f} & {lines[k]['avg_flow']:.0f} "
        f"& {lines[k]['saturated_hours']} & {gap(k):.1f} & {fmt(lines[k]['congestion_rent'])} \\\\" for k in lorder)
    write('tab_r1_lines.tex', rf"""\begin{{table*}}[!htbp]
\centering
\small
\caption{{Reference case 2024: use of the interconnections. Average flow in absolute value (MW), number of saturated hours, average price difference between the two ends (USD/MWh) and congestion rent (USD per day).}}\label{{tab:r1-lines}}
\begin{{tabular}}{{@{{}}lrrrrr@{{}}}}
\toprule
Line & NTC & Average flow & Saturated hours & Price difference & Congestion rent \\
\midrule
{rows}
\bottomrule
\end{{tabular}}
\end{{table*}}
""")

    # ── Figure R1-a : prix de chaque zone heure par heure ──
    draw_hourly(res, 'fig_r1_prices_hourly.png')

    # ── Figure R1-b : carte à 19 h ──
    draw_map(res, '19', 'fig_r1_map_19h.png')

    return res


# ══════════════════════════════════════════════════════════════════════════════════════════════════
# R2 — Valeur du couplage : zones isolées (toutes les NTC à zéro) contre zones couplées
# ══════════════════════════════════════════════════════════════════════════════════════════════════
def _energy(res):
    """Coût de production (MWh × prix offert), demande servie et non servie, par zone et au total,
    à partir du détail des segments (les blocs n'existent pas dans le cas de référence)."""
    out = {z: dict(cost=0.0, served=0.0, unserved=0.0) for z in ZONES}
    for g in res['summary']['segments']:
        for h, q in g['offered'].items():
            a = g['accepted'][h]
            if g['side'] == 'S':
                out[g['zone']]['cost'] += a * g['price']
            else:
                out[g['zone']]['served'] += a
                out[g['zone']]['unserved'] += q - a
    tot = {k: sum(out[z][k] for z in ZONES) for k in ('cost', 'served', 'unserved')}
    return out, tot


def r2():
    print('R2 — valeur du couplage')
    _, _, ntc = scenario_rows('reference_2024')
    cpl = run()
    iso = run(ntc={k: 0.0 for k in ntc})
    sc, si = cpl['summary'], iso['summary']
    ec, tc = _energy(cpl)
    ei, ti = _energy(iso)

    # ── Tableau R2-a : agrégats ──
    def line(lab, a, b, d=0, scale=1.0):
        return f"{lab} & {fmt(a / scale, d)} & {fmt(b / scale, d)} & {fmt((b - a) / scale, d)} \\\\"
    rows = '\n'.join([
        line('Production cost (M\\$)', ti['cost'], tc['cost'], 2, 1e6),
        line('Demand served (MWh)', ti['served'], tc['served']),
        line('Demand not served (MWh)', ti['unserved'], tc['unserved']),
        line('Consumer surplus (M\\$)', si['consumer_surplus'], sc['consumer_surplus'], 2, 1e6),
        line('Producer surplus (M\\$)', si['producer_surplus'], sc['producer_surplus'], 2, 1e6),
        line('Congestion rent (M\\$)', si['congestion_rent'], sc['congestion_rent'], 2, 1e6),
    ])
    write('tab_r2_aggregate.tex', rf"""\begin{{table}}[!htbp]
\centering
\small
\caption{{Value of the coupling: isolated zones (all capacities set to zero) and coupled zones, for one day.}}\label{{tab:r2-aggregate}}
\begin{{tabular}}{{@{{}}lrrr@{{}}}}
\toprule
 & Isolated & Coupled & Difference \\
\midrule
{rows}
\bottomrule
\end{{tabular}}
\end{{table}}
""")

    # ── Tableau R2-b : chaque zone ──
    zc, zi = sc['zones'], si['zones']
    d = {z: dict(dcs=zc[z]['consumer_surplus'] - zi[z]['consumer_surplus'],
                 dps=zc[z]['producer_surplus'] - zi[z]['producer_surplus'],
                 dun=ec[z]['unserved'] - ei[z]['unserved']) for z in ZONES}
    order = sorted(ZONES, key=lambda z: zc[z]['net_position'])        # des importateurs aux exportateurs
    rows = '\n'.join(
        f"{NAMES[z]} & {zi[z]['avg_price']:.0f} & {zc[z]['avg_price']:.0f} & {fmt(d[z]['dcs'] / 1e3)} & "
        f"{fmt(d[z]['dps'] / 1e3)} & {fmt((d[z]['dcs'] + d[z]['dps']) / 1e3)} & {fmt(d[z]['dun'])} & "
        f"{fmt(zc[z]['net_position'])} \\\\" for z in order)
    tot_cs = sum(d[z]['dcs'] for z in ZONES); tot_ps = sum(d[z]['dps'] for z in ZONES)
    rows += (f"\n\\midrule\nTotal & & & {fmt(tot_cs / 1e3)} & {fmt(tot_ps / 1e3)} & {fmt((tot_cs + tot_ps) / 1e3)} & "
             f"{fmt(sum(d[z]['dun'] for z in ZONES))} & \\\\")
    write('tab_r2_zones.tex', rf"""\begin{{table*}}[!htbp]
\centering
\small
\caption{{Value of the coupling for each zone: average price weighted by consumption (USD/MWh) when isolated and when coupled, change in consumer and producer surplus (thousand USD per day), change in demand not served (MWh per day) and net position in the coupled case (MWh per day, exports positive). The congestion rent, 1.37\,M\$ per day, is not allocated to the zones.}}\label{{tab:r2-zones}}
\begin{{tabular}}{{@{{}}lrrrrrrr@{{}}}}
\toprule
Zone & \multicolumn{{2}}{{c}}{{Price}} & \multicolumn{{3}}{{c}}{{Change in surplus}} & Change in demand & Net \\
\cmidrule(lr){{2-3}}\cmidrule(lr){{4-6}}
 & Isolated & Coupled & Consumers & Producers & Total & not served & position \\
\midrule
{rows}
\bottomrule
\end{{tabular}}
\end{{table*}}
""")

    # ── Figure R2 : transferts entre consommateurs et producteurs, par zone ──
    fig, ax = plt.subplots(figsize=(10, 4.2))
    x = range(len(order))
    ax.bar([i - 0.2 for i in x], [d[z]['dcs'] / 1e3 for z in order], width=0.4, color='#1f77b4', label='Consumers')
    ax.bar([i + 0.2 for i in x], [d[z]['dps'] / 1e3 for z in order], width=0.4, color='#ff7f0e', label='Producers')
    ax.scatter(list(x), [(d[z]['dcs'] + d[z]['dps']) / 1e3 for z in order], color='black', zorder=3, s=18,
               label='Total')
    ax.axhline(0, color='black', lw=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels([NAMES[z] for z in order], rotation=40, ha='right', fontsize=8)
    ax.set_ylabel('Change in surplus (thousand USD per day)')
    n_imp = sum(1 for z in order if zc[z]['net_position'] < 0)
    ax.axvline(n_imp - 0.5, color='grey', ls='--', lw=0.8)
    ax.text(n_imp - 0.6, ax.get_ylim()[1] * 0.92, 'importers', ha='right', fontsize=8, color='grey')
    ax.text(n_imp - 0.4, ax.get_ylim()[1] * 0.92, 'exporters', ha='left', fontsize=8, color='grey')
    ax.legend(fontsize=8, loc='lower left')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig_r2_transfers.png'), dpi=200)
    plt.close(fig)
    print('  écrit fig_r2_transfers.png')
    return cpl, iso


# ══════════════════════════════════════════════════════════════════════════════════════════════════
# R3 — Valeur des interconnexions : multiplicateurs des lignes et renforcement de 100 MW
# ══════════════════════════════════════════════════════════════════════════════════════════════════
DELTA_MW = 100


def _marginal_value(res, k):
    """Valeur marginale d'un MW de capacité sur la ligne k, en USD par jour : somme sur les heures du
    multiplicateur de la contrainte de capacité, c'est-à-dire de l'écart de prix entre les deux extrémités
    aux heures où la ligne est saturée (eq. cond-line du paper ; nul aux heures où elle ne l'est pas)."""
    u, v = k.split('->')
    cap = res['summary']['lines'][k]['ntc']
    val = 0.0
    for h, f in res['flows'][k].items():
        if cap > 0 and abs(f) >= cap - 0.1 - F_TOL:
            val += abs(res['prices'][v][h] - res['prices'][u][h])
    return val


def r3():
    import engine.clearing as C
    print('R3 — valeur des interconnexions')
    _, _, ntc = scenario_rows('reference_2024')
    base = run()
    _, tb = _energy(base)
    Wb = base['summary']['welfare']
    alpha_lines = {f"{u}->{v}" for u, v in C.ALPHA_LINES}

    rows = []
    for (u, v), cap in ntc.items():
        k = f"{u}->{v}"
        mv = _marginal_value(base, k)                         # USD par MW et par jour
        caps = dict(ntc); caps[(u, v)] = cap + DELTA_MW
        r = run(ntc=caps)
        _, t = _energy(r)
        rows.append(dict(k=k, ntc=cap, mv=mv, est=mv * DELTA_MW, dW=r['summary']['welfare'] - Wb,
                         dcost=t['cost'] - tb['cost'], dun=t['unserved'] - tb['unserved']))

    # Contrainte α du Burkina Faso : valeur de sa suppression (α = 1)
    old = C.ALPHA
    try:
        C.ALPHA = 1.0
        ra = run()
    finally:
        C.ALPHA = old
    _, ta = _energy(ra)
    alpha = dict(dW=ra['summary']['welfare'] - Wb, dcost=ta['cost'] - tb['cost'], dun=ta['unserved'] - tb['unserved'],
                 bfa_before=base['summary']['zones']['BFA']['avg_price'], bfa_after=ra['summary']['zones']['BFA']['avg_price'])

    rows.sort(key=lambda r: -r['dW'])
    star = '$^\\ast$'                                      # mark of the two lines under the joint import limit
    body = '\n'.join(
        f"{NAMES[r['k'].split('->')[0]]}--{NAMES[r['k'].split('->')[1]]}{star if r['k'] in alpha_lines else ''} & "
        f"{r['ntc']:.0f} & {fmt(r['mv'])} & {fmt(r['est'] / 1e3)} & {fmt(r['dW'] / 1e3)} & "
        f"{fmt(r['dcost'] / 1e3)} & {fmt(r['dun'])} \\\\" for r in rows)
    write('tab_r3_lines.tex', rf"""\begin{{table*}}[!htbp]
\centering
\small
\caption{{Value of the interconnections in the reference case. Marginal value: sum over the day of the multiplier of the capacity constraint, that is, of the price difference at the hours when the line is saturated (USD per MW and per day). Estimate: marginal value times {DELTA_MW}\,MW. The last three columns give the change obtained by clearing the market again with {DELTA_MW}\,MW more on the line: welfare and production cost (thousand USD per day) and demand not served (MWh per day). $^\ast$: line limited by the joint import constraint of Burkina Faso.}}\label{{tab:r3-lines}}
\begin{{tabular}}{{@{{}}lrrrrrr@{{}}}}
\toprule
Line & NTC & Marginal & Estimate & \multicolumn{{3}}{{c}}{{With {DELTA_MW}\,MW more}} \\
\cmidrule(lr){{5-7}}
 & (MW) & value & & Welfare & Cost & Not served \\
\midrule
{body}
\midrule
\multicolumn{{4}}{{@{{}}l}}{{Joint import limit of Burkina Faso removed ($\alpha = 1$)}} & {fmt(alpha['dW'] / 1e3)} & {fmt(alpha['dcost'] / 1e3)} & {fmt(alpha['dun'])} \\
\bottomrule
\end{{tabular}}
\end{{table*}}
""")

    # Figure R3 : estimation par le multiplicateur et gain obtenu, ligne par ligne
    top = [r for r in rows if r['est'] > 0 or r['dW'] > 1]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    x = range(len(top))
    ax.bar([i - 0.2 for i in x], [r['est'] / 1e3 for r in top], width=0.4, color='#9ecae1',
           label=f'Estimate: marginal value × {DELTA_MW} MW')
    ax.bar([i + 0.2 for i in x], [r['dW'] / 1e3 for r in top], width=0.4, color='#08519c',
           label=f'Welfare gain with {DELTA_MW} MW more (new clearing)')
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{NAMES[r['k'].split('->')[0]]}–{NAMES[r['k'].split('->')[1]]}" for r in top],
                       rotation=35, ha='right', fontsize=8)
    ax.set_ylabel('Thousand USD per day')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig_r3_lines.png'), dpi=200)
    plt.close(fig)
    print('  écrit fig_r3_lines.png')
    return rows, alpha


# ══════════════════════════════════════════════════════════════════════════════════════════════════
# R4 — Robustesse : les quatre scénarios, qui changent chacun un seul élément du cas de référence
# ══════════════════════════════════════════════════════════════════════════════════════════════════
SCEN = [('reference_2024', 'Reference'), ('secheresse_hydro', 'Hydro drought'),
        ('ligne_nga_ben', 'Nigeria–Benin out'), ('gaz_cher', 'Expensive gas'), ('forte_demande', 'High demand')]


def r4():
    print('R4 — scénarios')
    res = {k: run(k) for k, _ in SCEN}
    en = {k: _energy(r)[1] for k, r in res.items()}
    ref = res['reference_2024']['summary']

    # ── Tableau R4-a : agrégats de chaque scénario ──
    def sat(s):
        return sum(1 for l in s['lines'].values() if l['saturated_hours'] > 0)
    cols = ' & '.join(lab for _, lab in SCEN)
    def row(lab, f, d=0):
        return lab + ' & ' + ' & '.join(f(k) for k, _ in SCEN) + ' \\\\'
    rows = '\n'.join([
        row('Production cost (M\\$)', lambda k: f"{en[k]['cost'] / 1e6:.2f}"),
        row('Demand served (MWh)', lambda k: fmt(en[k]['served'])),
        row('Demand not served (MWh)', lambda k: fmt(en[k]['unserved'])),
        row('Congestion rent (M\\$)', lambda k: f"{res[k]['summary']['congestion_rent'] / 1e6:.2f}"),
        row('Lines saturated at least one hour', lambda k: str(sat(res[k]['summary']))),
    ])
    write('tab_r4_aggregate.tex', rf"""\begin{{table*}}[!htbp]
\centering
\small
\caption{{Scenarios: aggregate results for one day. Each scenario changes a single element of the reference case: hydropower availability halved; Nigeria--Benin line out of service; price of gas-fired plants increased by 40\,\%; demand increased by 15\,\% in all zones.}}\label{{tab:r4-aggregate}}
\begin{{tabular}}{{@{{}}l{'r' * len(SCEN)}@{{}}}}
\toprule
 & {cols} \\
\midrule
{rows}
\bottomrule
\end{{tabular}}
\end{{table*}}
""")

    # ── Tableau R4-b : prix moyen pondéré et position nette de chaque zone ──
    order = sorted(ZONES, key=lambda z: -ref['zones'][z]['avg_price'])
    rows = '\n'.join(
        f"{NAMES[z]} & " + ' & '.join(f"{res[k]['summary']['zones'][z]['avg_price']:.0f}" for k, _ in SCEN) + ' & '
        + ' & '.join(fmt(res[k]['summary']['zones'][z]['net_position']) for k, _ in SCEN) + ' \\\\' for z in order)
    write('tab_r4_zones.tex', rf"""\begin{{table*}}[!htbp]
\centering
\scriptsize
\caption{{Scenarios: average price weighted by consumption (USD/MWh) and net position (MWh per day, exports positive) of each zone. Columns: reference, hydro drought, Nigeria--Benin line out, expensive gas, high demand.}}\label{{tab:r4-zones}}
\begin{{tabular}}{{@{{}}l{'r' * len(SCEN)}{'r' * len(SCEN)}@{{}}}}
\toprule
Zone & \multicolumn{{{len(SCEN)}}}{{c}}{{Price}} & \multicolumn{{{len(SCEN)}}}{{c}}{{Net position}} \\
\cmidrule(lr){{2-{1 + len(SCEN)}}}\cmidrule(lr){{{2 + len(SCEN)}-{1 + 2 * len(SCEN)}}}
 & Ref. & Dro. & Line & Gas & Dem. & Ref. & Dro. & Line & Gas & Dem. \\
\midrule
{rows}
\bottomrule
\end{{tabular}}
\end{{table*}}
""")

    # ── Figure R4 : prix moyen de chaque zone dans chaque scénario ──
    fig, ax = plt.subplots(figsize=(10, 4.2))
    markers = ['o', 'v', 's', 'D', '^']
    for (k, lab), mk in zip(SCEN, markers):
        ax.plot(range(len(order)), [res[k]['summary']['zones'][z]['avg_price'] for z in order], mk,
                ms=6 if k == 'reference_2024' else 5, label=lab,
                color='black' if k == 'reference_2024' else None, mfc='none' if k != 'reference_2024' else 'black')
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([NAMES[z] for z in order], rotation=40, ha='right', fontsize=8)
    ax.set_ylabel('Average price (USD/MWh)')
    ax.legend(fontsize=8, ncol=3)
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig_r4_prices.png'), dpi=200)
    plt.close(fig)
    print('  écrit fig_r4_prices.png')
    return res


# ══════════════════════════════════════════════════════════════════════════════════════════════════
# R5 — Ordres complexes : un scénario d'évolution qui utilise ensemble toutes les options du marché
# ══════════════════════════════════════════════════════════════════════════════════════════════════
# Acteurs et valeurs hypothétiques (premières hypothèses), ajoutés au cas de référence 2024 : définis dans
# engine/scenarios.py (COMPLEX_ORDERS_*), avec les tests qui les utilisent.


def r5():
    import time
    from engine.checks import verify_result
    print('R5 — ordres complexes')
    blocks, mic = complex_orders_rows()
    base = run()
    t0 = time.time()
    res = run(block_rows=blocks, mic_rows=mic)
    elapsed = time.time() - t0
    s = res['summary']; d = s['diagnostics']
    problems = verify_result(res)

    # ── Tableau R5-a : ordres blocs soumis et résultat ──
    kind = {n: k for _, n, *_, k in COMPLEX_ORDERS_BLOCKS}

    def status_label(b):
        """Statut du bloc ; un PRB jugé sur la famille de blocs liés est marqué comme tel."""
        return 'PRB (family)' if b['status'] == 'PRB' and b.get('prb_basis') == 'family' else b['status']
    st = {b['name']: b for b in s['blocks']}
    rows = []
    for z, n, sd, q, p, h0, h1, par, g, k in COMPLEX_ORDERS_BLOCKS:
        b = st[n]
        rows.append(f"{n} & {NAMES[z]} & {k} & {h0:02d}--{h1 + 1:02d} & {q} & {p} & "
                    f"{'accepted' if b['accepted'] else 'rejected'} & {status_label(b)} & {fmt(b['surplus_if_accepted'] / 1e3, 1)} \\\\")
    write('tab_r5_blocks.tex', rf"""\begin{{table*}}[!htbp]
\centering
\small
\caption{{Scenario of complex orders added to the reference case (hypothetical actors and values). Hours: delivery period, from the start of the first hour to the end of the last one (18--22: four hours, from 18:00 to 22:00); surplus: surplus of the block at the final prices, whether accepted or not (thousand USD per day). PRB: paradoxically rejected block, tolerated as in EUPHEMIA; PRB (family): the family of linked blocks as a whole would have been profitable; in an exclusive group, a rejected block is assessed against the accepted one.}}\label{{tab:r5-blocks}}
\begin{{tabular}}{{@{{}}lllcrrllr@{{}}}}
\toprule
Order & Zone & Type & Hours & MW & Price & Result & Status & Surplus \\
\midrule
{chr(10).join(rows)}
\bottomrule
\end{{tabular}}
\end{{table*}}
""")

    # ── Tableau R5-b : conditions de revenu minimum ──
    # modifié par ENRICO : pour un producteur retiré, énergie, revenu et revenu requis au moment du retrait
    # (après le retrait ils valent zéro) ; taux de couverture = revenu / revenu requis.
    def mic_row(m):
        v = m['at_withdrawal'] if m['withdrawn'] and m.get('at_withdrawal') else m
        cov = v.get('coverage')
        cov_txt = '--' if cov is None else f"{cov:.2f}"
        outcome = 'withdrawn' if m['withdrawn'] else ('satisfied' if m['satisfied'] else 'not satisfied')
        return (f"{actor_name_en(m['actor'])} & {NAMES[m['zone']]} & {fmt(m['fixed_term'])} & {m['variable_term']:.0f} & "
                f"{fmt(v['accepted_mwh'])} & {fmt(v['income'])} & {fmt(v['required'])} & {cov_txt} & {outcome} \\\\")
    rows = '\n'.join(mic_row(m) for m in s['mic'])
    write('tab_r5_mic.tex', rf"""\begin{{table*}}[!htbp]
\centering
\small
\caption{{Minimum income conditions attached to three existing producers (hypothetical values): fixed term (USD), variable term (USD/MWh), accepted energy (MWh), income and required income (USD), and coverage, the ratio of income to required income. For a withdrawn producer, the values are those of the iteration at which its condition failed; for the others, those at the final prices.}}\label{{tab:r5-mic}}
\begin{{tabular}}{{@{{}}>{{\raggedright\arraybackslash}}p{{0.22\textwidth}}lrrrrrrl@{{}}}}
\toprule
Producer & Zone & Fixed & Variable & Energy & Income & Required & Coverage & Outcome \\
 & & term & term & & & income & & \\
\midrule
{rows}
\bottomrule
\end{{tabular}}
\end{{table*}}
""")

    # ── Tableau R5-c : effet sur les prix des zones concernées ──
    zs = sorted({z for z, *_ in COMPLEX_ORDERS_BLOCKS} | {z for z, *_ in COMPLEX_ORDERS_MIC}, key=lambda z: -base['summary']['zones'][z]['avg_price'])
    rows = '\n'.join(f"{NAMES[z]} & {base['summary']['zones'][z]['avg_price']:.0f} & {s['zones'][z]['avg_price']:.0f} & "
                     f"{fmt(base['summary']['zones'][z]['net_position'])} & {fmt(s['zones'][z]['net_position'])} \\\\" for z in zs)
    write('tab_r5_zones.tex', rf"""\begin{{table}}[!htbp]
\centering
\small
\caption{{Scenario of complex orders: average price weighted by consumption (USD/MWh) and net position (MWh per day) of the zones concerned, in the reference case and with the complex orders.}}\label{{tab:r5-zones}}
\begin{{tabular}}{{@{{}}lrrrr@{{}}}}
\toprule
Zone & \multicolumn{{2}}{{c}}{{Price}} & \multicolumn{{2}}{{c}}{{Net position}} \\
\cmidrule(lr){{2-3}}\cmidrule(lr){{4-5}}
 & Reference & Scenario & Reference & Scenario \\
\midrule
{rows}
\bottomrule
\end{{tabular}}
\end{{table}}
""")

    # ── Déroulement de l'algorithme (pour le texte du paper) ──
    summary = (f"Iterations of the block loop: {d['pab_iterations']}; blocks fixed: {d['blocks_fixed']}\n"
               f"Iterations of the MIC loop: {d['mic_iterations']}; withdrawn: {d['mic_withdrawn']}\n"
               f"Run time: {elapsed:.1f} s; independent checker: {'no anomaly' if not problems else problems}\n"
               f"Notes: {d['notes']}\n")
    write('r5_run.txt', summary)
    print(summary)
    return res


if __name__ == '__main__':
    parts = {'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4, 'r5': r5}
    todo = sys.argv[1:] or list(parts)
    for p in todo:
        parts[p]()
