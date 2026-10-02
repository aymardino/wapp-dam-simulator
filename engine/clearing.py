"""
WAPP Day-Ahead Market Clearing Engine
Fidèle au notebook wapp_market_clearing_final1.ipynb

Architecture : P1 (Welfare LP) → P1bis (Volume tiebreaker LP) → P2 (Pricing LP)
Flux signés : une seule variable f[u,v,t] ∈ [-NTC, +NTC], strictement linéaire.
"""
import time
import logging
import numpy as np
from pyomo.environ import (
    ConcreteModel, Var, Objective, Constraint, ConstraintList,
    NonNegativeReals, Binary, value, SolverFactory, maximize, minimize
)

logger = logging.getLogger(__name__)

P_MIN, P_MAX = 0, 500
ALPHA = 0.7   # Facteur d'interdépendance CIV/GHA/BFA

ZONES = ['NGA','BEN','TGO','GHA','CIV','BFA','MLI','SEN','GIN','SLE','LBR','GNB','GMB','NER']

LINES = [
    ('NGA','BEN',800), ('NGA','NER',300), ('BEN','TGO',600),
    ('TGO','GHA',500), ('GHA','CIV',600), ('GHA','BFA',250),
    ('CIV','BFA',250), ('CIV','MLI',250), ('CIV','LBR',400),
    ('LBR','SLE',400), ('SLE','GIN',400), ('GIN','GNB',300),
    ('GNB','GMB',300), ('GMB','SEN',300), ('SEN','MLI',300),
]
NTC   = {(u,v): c for u,v,c in LINES}
PAIRS = list(NTC.keys())

# ── Profils horaires (exactement comme dans le notebook) ──────────
_HYDRO = [0.7,0.65,0.6,0.6,0.6,0.65,0.75,0.85,0.9,0.95,1.0,1.0,
           1.0,0.95,0.9,0.85,0.9,0.95,1.0,0.95,0.9,0.85,0.8,0.75]
_SOLAR = [0,0,0,0,0,0.05,0.2,0.45,0.7,0.85,0.95,1.0,
           1.0,0.95,0.85,0.7,0.45,0.2,0.05,0,0,0,0,0]

PROF = {
    'solar':    _SOLAR,
    'hydro':    _HYDRO,
    'baseload': [0.95]*24,
    'peaker':   [1.0]*24,
    'flat':     [1.0]*24,
}

LOAD_WA = [0.55,0.50,0.48,0.47,0.48,0.52,0.62,0.75,0.85,0.90,0.92,0.90,
            0.88,0.85,0.82,0.80,0.82,0.88,0.95,1.00,0.98,0.90,0.78,0.65]

# ── Données par défaut — fidèles au notebook ──────────────────────
# Format supply_24 : (name, zone, [(q,p),...], profile_array_24)
DEFAULT_SUPPLY_24 = [
    ("Mainstream Solar",  'NGA', [(400,18),(400,25)],                   _SOLAR),
    ("Egbin Gas",         'NGA', [(400,24),(300,28),(200,35),(100,48)], [0.95]*24),
    ("Delta Gas",         'NGA', [(300,27),(200,33),(100,42)],          [0.95]*24),
    ("Geregu",            'NGA', [(200,30),(200,36)],                   [0.95]*24),
    ("Afam VI",           'NGA', [(300,35),(200,44)],                   [0.95]*24),
    ("Olorunsogo",        'NGA', [(300,38),(200,48),(100,62)],          [1.0]*24),
    ("VRA Akosombo",      'GHA', [(500,22),(300,30),(100,40)],          _HYDRO),
    ("Sunon Asogli",      'GHA', [(200,48),(100,58)],                   [0.95]*24),
    ("Cenpower",          'GHA', [(150,55),(50,68)],                    [0.95]*24),
    ("Karpowership GHA",  'GHA', [(200,65),(200,78)],                   [1.0]*24),
    ("CI-Energies Hydro", 'CIV', [(350,22),(250,30)],                   _HYDRO),
    ("CIPREL",            'CIV', [(200,40),(150,48),(50,58)],           [0.95]*24),
    ("Azito",             'CIV', [(200,45),(100,55)],                   [0.95]*24),
    ("Aggreko CIV",       'CIV', [(60,85),(40,98)],                     [1.0]*24),
    ("OMVS Manantali",    'SEN', [(100,32),(50,42)],                    _HYDRO),
    ("OMVS Felou",        'MLI', [(80,34),(70,44)],                     _HYDRO),
    ("SENELEC Thermal",   'SEN', [(200,100),(150,120),(50,145)],        [1.0]*24),
    ("OMVG Kaleta",       'GIN', [(60,36),(40,48)],                     _HYDRO),
    ("EDG Garafiri",      'GIN', [(50,75),(50,88)],                     _HYDRO),
    ("ContourGlobal",     'TGO', [(60,90),(40,105)],                    [0.95]*24),
    ("CEB Nangbeto",      'BEN', [(30,95),(20,112)],                    _HYDRO),
    ("SONABEL Gen",       'BFA', [(80,130),(70,148)],                   [1.0]*24),
    ("EDM-SA Gen",        'MLI', [(100,125),(80,142),(20,160)],         [1.0]*24),
    ("NAWEC Gen",         'GMB', [(30,145),(20,162)],                   [1.0]*24),
    ("EAGB Gen",          'GNB', [(15,155),(15,170)],                   [1.0]*24),
    ("LEC Gen",           'LBR', [(40,138),(40,155)],                   [1.0]*24),
    ("EDSA Gen",          'SLE', [(30,145),(30,162)],                   [1.0]*24),
    ("NIGELEC Gen",       'NER', [(40,125),(40,140)],                   [1.0]*24),
]

# Format demand_24 : (name, zone, [(q,p),...])  — modulated by LOAD_WA
DEFAULT_DEMAND_24 = [
    ("TCN Nigeria",      'NGA', [(2000,200),(1000,140),(500,100)]),
    ("ECG Ghana",        'GHA', [(1000,190),(500,140),(300,110)]),
    ("NEDCO",            'GHA', [(250,170),(150,120)]),
    ("CIE Distribution", 'CIV', [(800,195),(500,145),(300,105)]),
    ("SBEE",             'BEN', [(200,185),(150,150),(50,110)]),
    ("CEET",             'TGO', [(150,180),(100,145),(50,110)]),
    ("SENELEC Demand",   'SEN', [(350,200),(250,160),(100,120)]),
    ("SONABEL Demand",   'BFA', [(250,210),(200,175),(50,130)]),
    ("EDM-SA Demand",    'MLI', [(250,205),(200,170),(100,130)]),
    ("NIGELEC Demand",   'NER', [(200,215),(100,175),(50,135)]),
    ("EDG Demand",       'GIN', [(200,185),(150,150),(50,110)]),
    ("EDSA Demand",      'SLE', [(80,195),(50,155),(20,115)]),
    ("LEC Demand",       'LBR', [(60,190),(40,150),(20,115)]),
    ("NAWEC Demand",     'GMB', [(40,200),(30,160),(10,120)]),
    ("EAGB Demand",      'GNB', [(25,205),(15,165),(10,125)]),
]

# ── Solveur ───────────────────────────────────────────────────────
def _get_solver():
    """Gurobi → HiGHS (appsi) → GLPK → CBC."""
    candidates = [
        ('gurobi',       lambda: SolverFactory('gurobi')),
        ('appsi_highs',  lambda: SolverFactory('appsi_highs')),
        ('glpk',         lambda: SolverFactory('glpk')),
        ('cbc',          lambda: SolverFactory('cbc')),
    ]
    for name, factory in candidates:
        try:
            s = factory()
            if s.available():
                return s, name
        except Exception:
            pass
    raise RuntimeError("Aucun solveur LP disponible. Installez HiGHS : pip install highspy")


# ── Construction des segments (fidèle au notebook) ────────────────
def _build_default_segments(T):
    """
    Construit seg_s24 et seg_d24 exactement comme dans le notebook.
    seg_s24[i] = (name, zone, k, q, p, profile_array, [q*profile[t] for t])
    seg_d24[i] = (name, zone, k, q, p, [q*LOAD_WA[t] for t])
    """
    seg_s24 = [
        (n, z, k, q, p, prof, [round(q * prof[t]) for t in T])
        for n, z, segs, prof in DEFAULT_SUPPLY_24
        for k, (q, p) in enumerate(segs)
    ]
    seg_d24 = [
        (n, z, k, q, p, [round(q * LOAD_WA[t]) for t in T])
        for n, z, segs in DEFAULT_DEMAND_24
        for k, (q, p) in enumerate(segs)
    ]
    return seg_s24, seg_d24


def _build_segments_from_db(supply_rows, demand_rows, T):
    """
    Construit seg_s24 / seg_d24 depuis les lignes de la DB.
    Les profils sont soit un nom clé ('solar', 'hydro', ...) soit une liste de 24 valeurs.
    """
    seg_s24 = []
    for r in supply_rows:
        prof_key = r.get('profile', 'baseload')
        prof = PROF.get(prof_key, PROF['baseload'])
        for k_offset in [0]:  # chaque row est déjà un segment
            q, p = r['quantity'], r['price']
            seg_s24.append((
                r['actor'], r['zone'], r['segment'], q, p,
                prof, [round(q * prof[t]) for t in T]
            ))

    seg_d24 = []
    for r in demand_rows:
        q, p = r['quantity'], r['price']
        seg_d24.append((
            r['actor'], r['zone'], r['segment'], q, p,
            [round(q * LOAD_WA[t]) for t in T]
        ))

    return seg_s24, seg_d24


# ── Moteur principal P1 → P1bis → P2 ─────────────────────────────
def run_clearing(supply_rows=None, demand_rows=None, horizon=24, ntc_override=None):
    """
    Clearing complet P1 → P1bis → P2.
    ntc_override : dict {(u,v): mw} — si None, utilise les NTC de la DB ou les valeurs par défaut.
    Retourne dict avec prices, flows, dispatch, welfare, volume, summary.
    """
    t_total = time.time()
    T = list(range(horizon))
    solver, solver_name = _get_solver()
    logger.info(f"Solveur : {solver_name}")

    # ── NTC : DB > override > défaut ──────────────────────────────
    active_ntc = dict(NTC)  # valeurs par défaut
    if ntc_override:
        active_ntc.update(ntc_override)
    else:
        try:
            from engine.db import get_ntc
            db_ntc = get_ntc()
            if db_ntc:
                active_ntc = db_ntc
        except Exception:
            pass

    PAIRS = list(active_ntc.keys())
    if supply_rows is None and demand_rows is None:
        seg_s24, seg_d24 = _build_default_segments(T)
    else:
        seg_s24, seg_d24 = _build_segments_from_db(
            supply_rows or [], demand_rows or [], T
        )

    NS24, ND24 = len(seg_s24), len(seg_d24)
    Si24 = range(NS24)
    Di24 = range(ND24)

    def Qs(s, t): return seg_s24[s][6][t] if t < len(seg_s24[s][6]) else 0
    def Qd(d, t): return seg_d24[d][5][t] if t < len(seg_d24[d][5]) else 0

    logger.info(f"Segments: {NS24} offres vente, {ND24} offres achat, horizon={horizon}h")

    # ══════════════════════════════════════════════════════════════
    # P1 : Maximisation du Welfare (LP — flux signés)
    # ══════════════════════════════════════════════════════════════
    m = ConcreteModel()
    m.xs = Var(Si24, T, bounds=(0, 1))
    m.xd = Var(Di24, T, bounds=(0, 1))
    # Flux signé : positif = sens (u→v), négatif = sens inverse
    m.f  = Var(PAIRS, T, bounds=lambda m, u, v, t: (-NTC[(u,v)], NTC[(u,v)]))

    m.obj = Objective(
        expr=sum(seg_d24[d][4] * Qd(d,t) * m.xd[d,t]
                 for t in T for d in Di24 if Qd(d,t) > 0)
           - sum(seg_s24[s][4] * Qs(s,t) * m.xs[s,t]
                 for t in T for s in Si24 if Qs(s,t) > 0),
        sense=maximize
    )

    def bal(m, z, t):
        p  = sum(Qs(s,t) * m.xs[s,t]
                 for s in Si24 if seg_s24[s][1] == z and Qs(s,t) > 0)
        c  = sum(Qd(d,t) * m.xd[d,t]
                 for d in Di24 if seg_d24[d][1] == z and Qd(d,t) > 0)
        ni = (sum(m.f[u,v,t] for u,v in PAIRS if v == z)
            - sum(m.f[u,v,t] for u,v in PAIRS if u == z))
        return p + ni == c

    m.bal     = Constraint(ZONES, T, rule=bal)
    m.interco = Constraint(T, rule=lambda m, t:
        m.f['GHA','BFA',t] + m.f['CIV','BFA',t]
        <= ALPHA * (NTC[('GHA','BFA')] + NTC[('CIV','BFA')]))

    solver.solve(m, tee=False)
    W_star = value(m.obj)
    logger.info(f"P1 : W* = {W_star:,.0f} EUR")

    # ══════════════════════════════════════════════════════════════
    # P1bis : Maximisation du Volume (tiebreaker)
    # ══════════════════════════════════════════════════════════════
    m2 = ConcreteModel()
    m2.xs = Var(Si24, T, bounds=(0, 1))
    m2.xd = Var(Di24, T, bounds=(0, 1))
    m2.f  = Var(PAIRS, T, bounds=lambda m, u, v, t: (-NTC[(u,v)], NTC[(u,v)]))

    m2.maxvol = Objective(
        expr=sum(Qs(s,t) * m2.xs[s,t] for t in T for s in Si24 if Qs(s,t) > 0)
           + sum(Qd(d,t) * m2.xd[d,t] for t in T for d in Di24 if Qd(d,t) > 0),
        sense=maximize
    )

    def bal1b(m, z, t):
        p  = sum(Qs(s,t) * m.xs[s,t]
                 for s in Si24 if seg_s24[s][1] == z and Qs(s,t) > 0)
        c  = sum(Qd(d,t) * m.xd[d,t]
                 for d in Di24 if seg_d24[d][1] == z and Qd(d,t) > 0)
        ni = (sum(m.f[u,v,t] for u,v in PAIRS if v == z)
            - sum(m.f[u,v,t] for u,v in PAIRS if u == z))
        return p + ni == c

    m2.bal  = Constraint(ZONES, T, rule=bal1b)
    m2.ic   = Constraint(T, rule=lambda m, t:
        m.f['GHA','BFA',t] + m.f['CIV','BFA',t]
        <= ALPHA * (NTC[('GHA','BFA')] + NTC[('CIV','BFA')]))
    m2.wfix = Constraint(expr=
        sum(seg_d24[d][4] * Qd(d,t) * m2.xd[d,t]
            for t in T for d in Di24 if Qd(d,t) > 0)
      - sum(seg_s24[s][4] * Qs(s,t) * m2.xs[s,t]
            for t in T for s in Si24 if Qs(s,t) > 0)
        >= W_star - 0.01
    )

    solver.solve(m2, tee=False)

    xs3 = {(s,t): (value(m2.xs[s,t]) if Qs(s,t) > 0 else 0)
           for s in Si24 for t in T}
    xd3 = {(d,t): (value(m2.xd[d,t]) if Qd(d,t) > 0 else 0)
           for d in Di24 for t in T}
    fl3 = {(u,v,t): value(m2.f[u,v,t]) for u,v in PAIRS for t in T}

    vol = sum(Qs(s,t) * xs3[s,t] for s in Si24 for t in T if Qs(s,t) > 0)
    logger.info(f"P1bis : Volume = {vol:,.0f} MWh")

    # ══════════════════════════════════════════════════════════════
    # P2 : Pricing LP (exactement comme dans le notebook)
    # ══════════════════════════════════════════════════════════════
    mp = ConcreteModel()
    mp.pi = Var(ZONES, T, bounds=(P_MIN, P_MAX))
    mp.ep = Var(ZONES, T, domain=NonNegativeReals)
    mp.en = Var(ZONES, T, domain=NonNegativeReals)

    pi_ref3 = {}
    for z in ZONES:
        for t in T:
            acc_s = [seg_s24[s][4] for s in Si24
                     if seg_s24[s][1] == z and Qs(s,t) > 0 and xs3[s,t] > 0.01]
            acc_d = [seg_d24[d][4] for d in Di24
                     if seg_d24[d][1] == z and Qd(d,t) > 0 and xd3[d,t] > 0.01]
            lb = max(acc_s) if acc_s else P_MIN
            ub = min(acc_d) if acc_d else P_MAX
            pi_ref3[z, t] = (lb + ub) / 2

    mp.obj2  = Objective(
        expr=sum(mp.ep[z,t] + mp.en[z,t] for z in ZONES for t in T),
        sense=minimize
    )
    mp.refc  = ConstraintList()
    for z in ZONES:
        for t in T:
            mp.refc.add(mp.pi[z,t] - pi_ref3[z,t] == mp.ep[z,t] - mp.en[z,t])

    mp.sc = ConstraintList()
    for s in Si24:
        z = seg_s24[s][1]
        for t in T:
            if Qs(s,t) > 0 and xs3[s,t] > 0.01:
                mp.sc.add(mp.pi[z,t] >= seg_s24[s][4])
            if Qs(s,t) > 0 and 0.01 < xs3[s,t] < 0.99:
                mp.sc.add(mp.pi[z,t] <= seg_s24[s][4])
    for d in Di24:
        z = seg_d24[d][1]
        for t in T:
            if Qd(d,t) > 0 and xd3[d,t] > 0.01:
                mp.sc.add(mp.pi[z,t] <= seg_d24[d][4])
            if Qd(d,t) > 0 and 0.01 < xd3[d,t] < 0.99:
                mp.sc.add(mp.pi[z,t] >= seg_d24[d][4])
    for u, v in PAIRS:
        for t in T:
            fval = fl3.get((u,v,t), 0)
            if fval > 0.1:
                mp.sc.add(mp.pi[v,t] >= mp.pi[u,t])
            elif fval < -0.1:
                mp.sc.add(mp.pi[u,t] >= mp.pi[v,t])

    solver.solve(mp, tee=False)

    # ── Collecte des résultats ─────────────────────────────────────
    prices = {z: {str(t): round(value(mp.pi[z,t]), 2) for t in T} for z in ZONES}

    # Flux : clé "u->v", valeur signée (positif = u vers v)
    flows = {}
    for u, v in PAIRS:
        key = f"{u}->{v}"
        flows[key] = {str(t): round(fl3[(u,v,t)], 1) for t in T}

    # Dispatch par profil (pour affichage empilé)
    profile_labels = {
        tuple(_SOLAR):    'solar',
        tuple([0.95]*24): 'baseload',
        tuple([1.0]*24):  'peaker',
        tuple(_HYDRO):    'hydro',
    }
    dispatch_by_prof = {k: [0.0]*horizon for k in ['solar','hydro','baseload','peaker','flat']}
    demand_accepted  = [0.0]*horizon

    for s in Si24:
        prof_arr = tuple(seg_s24[s][5])
        prof_label = profile_labels.get(prof_arr, 'baseload')
        for t in T:
            if Qs(s,t) > 0:
                dispatch_by_prof[prof_label][t] += Qs(s,t) * xs3[s,t]
    for d in Di24:
        for t in T:
            if Qd(d,t) > 0:
                demand_accepted[t] += Qd(d,t) * xd3[d,t]

    # Positions nettes (somme sur 24h)
    net_pos = {}
    for z in ZONES:
        gen  = sum(Qs(s,t) * xs3[s,t] for s in Si24 for t in T
                   if seg_s24[s][1] == z and Qs(s,t) > 0)
        load = sum(Qd(d,t) * xd3[d,t] for d in Di24 for t in T
                   if seg_d24[d][1] == z and Qd(d,t) > 0)
        net_pos[z] = round(gen - load, 1)

    # Welfare horaire
    welfare_hourly = [
        sum(seg_d24[d][4] * Qd(d,t) * xd3[d,t] for d in Di24 if Qd(d,t) > 0)
      - sum(seg_s24[s][4] * Qs(s,t) * xs3[s,t] for s in Si24 if Qs(s,t) > 0)
        for t in T
    ]
    W_final = sum(welfare_hourly)

    summary = {
        'welfare':         round(W_final, 0),
        'volume':          round(vol, 0),
        'elapsed':         round(time.time() - t_total, 2),
        'solver':          solver_name,
        'horizon':         horizon,
        'n_supply':        len(seg_s24),
        'n_demand':        len(seg_d24),
        'net_pos':         net_pos,
        'demand_accepted': demand_accepted,
        'welfare_hourly':  welfare_hourly,
    }

    dispatch_out = dict(dispatch_by_prof)
    dispatch_out['demand'] = demand_accepted

    logger.info(f"Clearing terminé en {summary['elapsed']}s | W={W_final:,.0f} EUR | Vol={vol:,.0f} MWh")
    return {
        'prices':   prices,
        'flows':    flows,
        'dispatch': dispatch_out,
        'welfare':  W_final,
        'volume':   vol,
        'summary':  summary,
    }
