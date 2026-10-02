"""
WAPP Day-Ahead Market Clearing Engine — v2 (octobre 2026)

Décomposition séquentielle du Livrable 2 (8 mars 2026) :
    P1    : maximisation du welfare (LP ; MILP en présence d'ordres bloc)
    P1bis : maximisation du volume parmi les solutions de welfare optimal (LP, départage)
    P2    : prix zonaux = prix admissibles les plus proches du milieu de l'intervalle (LP)

Changements v2 par rapport au moteur du Livrable 3 (détail dans CHANGELOG.md et docs/REGLES_DE_MARCHE.md) :
    - P2 « complet » : l'ensemble des prix admissibles est décrit par les conditions KKT complètes
      (ordres rejetés, égalité des prix sur les lignes non saturées, multiplicateur de la contrainte α).
      Le mode 'l2' conserve les contraintes (8)-(12) du Livrable 2 pour comparaison.
    - P1bis exact (ε = 0) au lieu de ε = 0,01 ; repli documenté si le solveur ne suit pas.
    - Ordres bloc, liés et exclusifs (MILP) portés du notebook wapp_market_clearing_final1.ipynb ;
      boucle de rejet des blocs paradoxalement acceptés (règle EUPHEMIA) ; PRB signalés.
    - NTC paramétrables, heures simulées paramétrables, zones manquantes complétées par les
      données de référence, validation des entrées.
    - Contrôle du statut du solveur à chaque étape (ClearingError) et diagnostics de cohérence.
    - Règle explicite de partage des offres au même prix (prorata par défaut) après P1bis.
    - Minimum Income Condition (revenu ≥ terme fixe + terme variable × volume) avec retrait itératif.
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

from pyomo.environ import (
    ConcreteModel, Var, Objective, Constraint, ConstraintList, Expression,
    NonNegativeReals, Binary, value, SolverFactory, maximize, minimize
)
from pyomo.opt import TerminationCondition as _TC

logger = logging.getLogger(__name__)

__all__ = [
    'run_clearing', 'ClearingError', 'default_rows', 'validate_inputs',
    'ZONES', 'LINES', 'NTC', 'PAIRS', 'PROF', 'LOAD_WA', 'ALPHA', 'ALPHA_LINES',
    'P_MIN', 'P_MAX', 'DEFAULT_SUPPLY_24', 'DEFAULT_DEMAND_24',
    'PRICING_MODES', 'PAB_RULES', 'TIE_RULES',
]

# ── Paramètres réglementaires et numériques ───────────────────────
P_MIN, P_MAX = 0, 500      # bornes de prix (Livrable 2, tableau 2)
ALPHA = 0.7                # facteur d'interdépendance CIV/GHA/BFA (contrainte C4)
X_TOL = 1e-4               # fraction : x < X_TOL = rejeté, x > 1 - X_TOL = accepté en totalité
F_TOL = 1e-3               # MW : une ligne est saturée si |f| >= NTC - F_TOL
PRICE_TOL = 0.5            # EUR/MWh : tolérance des diagnostics de cohérence
PRICING_MODES = ('complete', 'l2')
PAB_RULES = ('euphemia', 'l2', 'none')
TIE_RULES = ('prorata', 'order', 'solver')   # partage des offres au même prix
MIC_TOL = 0.5              # unité monétaire : tolérance de la condition de revenu minimum

ZONES = ['NGA','BEN','TGO','GHA','CIV','BFA','MLI','SEN','GIN','SLE','LBR','GNB','GMB','NER']

LINES = [
    ('NGA','BEN',800), ('NGA','NER',300), ('BEN','TGO',600),
    ('TGO','GHA',500), ('GHA','CIV',600), ('GHA','BFA',250),
    ('CIV','BFA',250), ('CIV','MLI',250), ('CIV','LBR',400),
    ('LBR','SLE',400), ('SLE','GIN',400), ('GIN','GNB',300),
    ('GNB','GMB',300), ('GMB','SEN',300), ('SEN','MLI',300),
]
NTC   = {(u, v): c for u, v, c in LINES}
PAIRS = list(NTC.keys())
ALPHA_LINES = (('GHA', 'BFA'), ('CIV', 'BFA'))

# ── Profils horaires (Livrable 2, tableaux 12 et 13) ──────────────
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

# ── Données de référence (notebook / Livrable 2, step 3) ──────────
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

REFERENCE_PLAYER = 'Référence'


class ClearingError(Exception):
    """Erreur de clearing avec un message lisible pour l'administrateur."""


# ── Structures internes ───────────────────────────────────────────
@dataclass
class Seg:
    actor: str
    zone: str
    k: int
    q: float
    p: float
    profile: str
    qty: dict                 # {heure: quantité effective}
    player: str = ''
    side: str = 'S'


@dataclass
class Block:
    name: str
    zone: str
    side: str                 # 'S' vente, 'D' achat
    q: float
    p: float
    hours: list
    parent: Optional[str] = None
    group: Optional[str] = None
    player: str = ''
    active_hours: list = field(default_factory=list)


def _profile_name(arr):
    """Nom du profil pour un vecteur de 24 valeurs (peaker a priorité sur flat, identiques)."""
    t = tuple(arr)
    for name in ('solar', 'hydro', 'baseload', 'peaker'):
        if tuple(PROF[name]) == t:
            return name
    return 'custom'


def _profile_array(prof):
    """Accepte un nom de profil ou un vecteur de 24 valeurs. Retourne (vecteur, nom)."""
    if prof is None:
        return PROF['baseload'], 'baseload'
    if isinstance(prof, str):
        if prof in PROF:
            return PROF[prof], prof
        raise ClearingError(f"Profil horaire inconnu : '{prof}' (attendu : {', '.join(PROF)}).")
    arr = [float(v) for v in prof]
    if len(arr) != 24:
        raise ClearingError("Un profil horaire personnalisé doit contenir 24 valeurs.")
    return arr, _profile_name(arr)


def default_rows(zones=None):
    """Données de référence au format des lignes de la base (offres et demandes)."""
    sup, dem = [], []
    for n, z, segs, prof in DEFAULT_SUPPLY_24:
        if zones is not None and z not in zones:
            continue
        for k, (q, p) in enumerate(segs):
            sup.append(dict(zone=z, player=REFERENCE_PLAYER, actor=n, segment=k,
                            quantity=q, price=p, profile=_profile_name(prof)))
    for n, z, segs in DEFAULT_DEMAND_24:
        if zones is not None and z not in zones:
            continue
        for k, (q, p) in enumerate(segs):
            dem.append(dict(zone=z, player=REFERENCE_PLAYER, actor=n, segment=k,
                            quantity=q, price=p))
    return sup, dem


# ── Validation des entrées ────────────────────────────────────────
def validate_inputs(supply_rows, demand_rows, block_rows):
    """Lève ClearingError avec un message précis si une entrée est hors spécification."""
    for kind, rows in (('vente', supply_rows), ('achat', demand_rows)):
        for r in rows:
            who = f"{r.get('actor', '?')} ({r.get('zone', '?')})"
            if r.get('zone') not in ZONES:
                raise ClearingError(f"Offre de {kind} {who} : zone inconnue.")
            q, p = float(r.get('quantity', 0)), float(r.get('price', 0))
            if q < 0:
                raise ClearingError(f"Offre de {kind} {who} : quantité négative.")
            if not (P_MIN <= p <= P_MAX):
                raise ClearingError(f"Offre de {kind} {who} : prix {p:g} hors des bornes [{P_MIN}, {P_MAX}].")
    for r in block_rows:
        who = f"{r.get('name', '?')} ({r.get('zone', '?')})"
        if r.get('zone') not in ZONES:
            raise ClearingError(f"Bloc {who} : zone inconnue.")
        if r.get('side') not in ('S', 'D'):
            raise ClearingError(f"Bloc {who} : sens attendu 'S' (vente) ou 'D' (achat).")
        q, p = float(r.get('quantity', 0)), float(r.get('price', 0))
        if q < 0:
            raise ClearingError(f"Bloc {who} : quantité négative.")
        if not (P_MIN <= p <= P_MAX):
            raise ClearingError(f"Bloc {who} : prix {p:g} hors des bornes [{P_MIN}, {P_MAX}].")
        h0, h1 = int(r.get('h_start', 0)), int(r.get('h_end', 23))
        if not (0 <= h0 <= 23 and 0 <= h1 <= 23 and h0 <= h1):
            raise ClearingError(f"Bloc {who} : plage horaire invalide ({h0}-{h1}).")


# ── Construction des segments et des blocs ────────────────────────
def _build_segments(supply_rows, demand_rows, hours):
    seg_s, seg_d = [], []
    for r in supply_rows:
        arr, name = _profile_array(r.get('profile', 'baseload'))
        q, p = float(r['quantity']), float(r['price'])
        seg_s.append(Seg(r['actor'], r['zone'], int(r.get('segment', 0)), q, p, name,
                         {h: round(q * arr[h]) for h in hours}, r.get('player', ''), 'S'))
    for r in demand_rows:
        q, p = float(r['quantity']), float(r['price'])
        seg_d.append(Seg(r['actor'], r['zone'], int(r.get('segment', 0)), q, p, 'load',
                         {h: round(q * LOAD_WA[h]) for h in hours}, r.get('player', ''), 'D'))
    return seg_s, seg_d


def _build_blocks(block_rows, hours):
    hours_set = set(hours)
    blocks = []
    for r in block_rows:
        h0, h1 = int(r.get('h_start', 0)), int(r.get('h_end', 23))
        hb = list(range(h0, h1 + 1))
        blocks.append(Block(name=r['name'], zone=r['zone'], side=r['side'],
                            q=float(r['quantity']), p=float(r['price']), hours=hb,
                            parent=(r.get('parent_name') or None), group=(r.get('excl_group') or None),
                            player=r.get('player', ''), active_hours=[h for h in hb if h in hours_set]))
    return blocks


def _resolve_links(blocks, notes):
    """Parent par nom au sein du même (zone, trader) ; groupes exclusifs idem."""
    index = {}
    for i, b in enumerate(blocks):
        index.setdefault((b.zone, b.player, b.name), i)
    parent_of = {}
    for i, b in enumerate(blocks):
        if b.parent:
            j = index.get((b.zone, b.player, b.parent))
            if j is None or j == i:
                notes.append(f"Bloc '{b.name}' : parent '{b.parent}' introuvable, lien ignoré.")
            else:
                parent_of[i] = j
    groups = {}
    for i, b in enumerate(blocks):
        if b.group:
            groups.setdefault((b.zone, b.player, b.group), []).append(i)
    return parent_of, [g for g in groups.values() if len(g) > 1]


# ── Solveur ───────────────────────────────────────────────────────
def _get_solver():
    """Gurobi → HiGHS (appsi) → GLPK → CBC. Retourne (solveur, nom)."""
    candidates = [
        ('gurobi',      lambda: SolverFactory('gurobi')),
        ('appsi_highs', lambda: SolverFactory('appsi_highs')),
        ('glpk',        lambda: SolverFactory('glpk')),
        ('cbc',         lambda: SolverFactory('cbc')),
    ]
    for name, factory in candidates:
        try:
            s = factory()
            if s.available():
                try:
                    if name == 'gurobi':
                        s.options['MIPGap'] = 1e-6
                    elif name == 'appsi_highs':
                        s.options['mip_rel_gap'] = 1e-6
                except Exception:
                    pass
                return s, name
        except Exception:
            pass
    raise ClearingError("Aucun solveur disponible. Installez HiGHS : pip install highspy")


_OK = (_TC.optimal, _TC.globallyOptimal, _TC.locallyOptimal)


def _try_solve(solver, model):
    """Résout sans charger la solution ; charge si optimal. Retourne (ok, statut)."""
    try:
        res = solver.solve(model, load_solutions=False, tee=False)
    except Exception as e:                       # erreur interne du solveur
        return False, f"erreur solveur : {e}"
    tc = res.solver.termination_condition
    if tc in _OK:
        model.solutions.load_from(res)
        return True, str(tc)
    return False, str(tc)


def _solve(solver, model, label):
    ok, status = _try_solve(solver, model)
    if not ok:
        raise ClearingError(f"{label} : pas de solution optimale ({status}).")
    return status


# ── Modèle primal (P1 / P1bis) ────────────────────────────────────
def _build_primal(seg_s, seg_d, blocks, parent_of, groups, hours, ntc, pairs,
                  objective='welfare', welfare_floor=None, fixed_y=None):
    S, D, B = range(len(seg_s)), range(len(seg_d)), range(len(blocks))
    m = ConcreteModel()
    m.xs = Var(S, hours, bounds=(0, 1))
    m.xd = Var(D, hours, bounds=(0, 1))
    m.f = Var(pairs, hours, bounds=lambda m, u, v, h: (-ntc[(u, v)], ntc[(u, v)]))
    if blocks:
        m.yb = Var(B, domain=Binary)
        for b in B:
            if not blocks[b].active_hours:
                m.yb[b].fix(0)
        if fixed_y:
            for b, v in fixed_y.items():
                m.yb[b].fix(v)

    def welfare_rule(m):
        w = sum(seg_d[d].p * seg_d[d].qty[h] * m.xd[d, h] for h in hours for d in D if seg_d[d].qty[h] > 0) \
          - sum(seg_s[s].p * seg_s[s].qty[h] * m.xs[s, h] for h in hours for s in S if seg_s[s].qty[h] > 0)
        for b in B:
            n = len(blocks[b].active_hours)
            if n == 0:
                continue
            term = blocks[b].p * blocks[b].q * n * m.yb[b]
            w = w + term if blocks[b].side == 'D' else w - term
        return w
    m.welfare = Expression(rule=welfare_rule)

    def bal(m, z, h):
        terms = [seg_s[s].qty[h] * m.xs[s, h] for s in S if seg_s[s].zone == z and seg_s[s].qty[h] > 0]
        terms += [-seg_d[d].qty[h] * m.xd[d, h] for d in D if seg_d[d].zone == z and seg_d[d].qty[h] > 0]
        terms += [m.f[u, v, h] for u, v in pairs if v == z]
        terms += [-m.f[u, v, h] for u, v in pairs if u == z]
        for b in B:
            if blocks[b].zone == z and h in blocks[b].active_hours:
                terms.append((blocks[b].q if blocks[b].side == 'S' else -blocks[b].q) * m.yb[b])
        if not terms:
            return Constraint.Skip
        return sum(terms) == 0
    m.bal = Constraint(ZONES, hours, rule=bal)

    if all(l in ntc for l in ALPHA_LINES):
        cap = ALPHA * sum(ntc[l] for l in ALPHA_LINES)
        m.alpha = Constraint(hours, rule=lambda m, h:
                             sum(m.f[u, v, h] for u, v in ALPHA_LINES) <= cap)

    if blocks:
        m.linked = ConstraintList()
        for child, parent in parent_of.items():
            m.linked.add(m.yb[child] <= m.yb[parent])
        m.excl = ConstraintList()
        for g in groups:
            m.excl.add(sum(m.yb[b] for b in g) <= 1)

    if objective == 'welfare':
        m.obj = Objective(expr=m.welfare, sense=maximize)
    else:
        m.obj = Objective(expr=sum(seg_s[s].qty[h] * m.xs[s, h] for h in hours for s in S if seg_s[s].qty[h] > 0)
                               + sum(seg_d[d].qty[h] * m.xd[d, h] for h in hours for d in D if seg_d[d].qty[h] > 0),
                          sense=maximize)
        m.wfloor = Constraint(expr=m.welfare >= welfare_floor)
    return m


def _extract(m, seg_s, seg_d, blocks, hours, pairs):
    xs = {(s, h): (float(value(m.xs[s, h])) if seg_s[s].qty[h] > 0 else 0.0)
          for s in range(len(seg_s)) for h in hours}
    xd = {(d, h): (float(value(m.xd[d, h])) if seg_d[d].qty[h] > 0 else 0.0)
          for d in range(len(seg_d)) for h in hours}
    fl = {(u, v, h): float(value(m.f[u, v, h])) for u, v in pairs for h in hours}
    y = {b: int(round(value(m.yb[b]))) for b in range(len(blocks))} if blocks else {}
    return xs, xd, fl, y


# ── P2 : prix zonaux ──────────────────────────────────────────────
def _classify(x):
    if x > 1 - X_TOL:
        return 'acc'
    if x < X_TOL:
        return 'rej'
    return 'part'


def _reference_prices(seg_s, seg_d, xs, xd, hours, mode):
    """Prix de référence = milieu de l'intervalle admissible local (Livrable 2 §2.4).
    'l2' : bornes données par les seuls ordres acceptés ; 'complete' : les ordres rejetés
    resserrent aussi l'intervalle (vente rejetée => borne haute, achat rejeté => borne basse)."""
    ref, bounds = {}, {}
    for z in ZONES:
        for h in hours:
            lo, hi = P_MIN, P_MAX
            for s in seg_s:
                pass
            lo_c, hi_c = [], []
            for i, s in enumerate(seg_s):
                if s.zone != z or s.qty[h] <= 0:
                    continue
                x = xs[i, h]
                if mode == 'l2':
                    if x > 0.01:
                        lo_c.append(s.p)
                else:
                    c = _classify(x)
                    if c in ('acc', 'part'):
                        lo_c.append(s.p)
                    else:
                        hi_c.append(s.p)
            for i, d in enumerate(seg_d):
                if d.zone != z or d.qty[h] <= 0:
                    continue
                x = xd[i, h]
                if mode == 'l2':
                    if x > 0.01:
                        hi_c.append(d.p)
                else:
                    c = _classify(x)
                    if c in ('acc', 'part'):
                        hi_c.append(d.p)
                    else:
                        lo_c.append(d.p)
            lo = max(lo_c) if lo_c else P_MIN
            hi = min(hi_c) if hi_c else P_MAX
            bounds[z, h] = (lo, hi)
            ref[z, h] = (lo + hi) / 2
    return ref, bounds


def _build_pricing(seg_s, seg_d, xs, xd, fl, hours, ntc, pairs, alpha_active, mode):
    ref, _ = _reference_prices(seg_s, seg_d, xs, xd, hours, mode)
    mp = ConcreteModel()
    mp.pi = Var(ZONES, hours, bounds=(P_MIN, P_MAX))
    mp.ep = Var(ZONES, hours, domain=NonNegativeReals)
    mp.en = Var(ZONES, hours, domain=NonNegativeReals)
    mp.obj = Objective(expr=sum(mp.ep[z, h] + mp.en[z, h] for z in ZONES for h in hours), sense=minimize)
    mp.refc = ConstraintList()
    for z in ZONES:
        for h in hours:
            mp.refc.add(mp.pi[z, h] - ref[z, h] == mp.ep[z, h] - mp.en[z, h])
    mp.sc = ConstraintList()
    if mode == 'l2':
        # Contraintes (8)-(12) du Livrable 2, telles qu'implémentées dans le notebook
        for i, s in enumerate(seg_s):
            for h in hours:
                if s.qty[h] <= 0:
                    continue
                x = xs[i, h]
                if x > 0.01:
                    mp.sc.add(mp.pi[s.zone, h] >= s.p)
                if 0.01 < x < 0.99:
                    mp.sc.add(mp.pi[s.zone, h] <= s.p)
        for i, d in enumerate(seg_d):
            for h in hours:
                if d.qty[h] <= 0:
                    continue
                x = xd[i, h]
                if x > 0.01:
                    mp.sc.add(mp.pi[d.zone, h] <= d.p)
                if 0.01 < x < 0.99:
                    mp.sc.add(mp.pi[d.zone, h] >= d.p)
        for u, v in pairs:
            for h in hours:
                f = fl[u, v, h]
                if f > 0.1:
                    mp.sc.add(mp.pi[v, h] >= mp.pi[u, h])
                elif f < -0.1:
                    mp.sc.add(mp.pi[u, h] >= mp.pi[v, h])
        return mp

    # Mode 'complete' : conditions KKT complètes
    for i, s in enumerate(seg_s):
        for h in hours:
            if s.qty[h] <= 0:
                continue
            c = _classify(xs[i, h])
            if c == 'acc':
                mp.sc.add(mp.pi[s.zone, h] >= s.p)
            elif c == 'rej':
                mp.sc.add(mp.pi[s.zone, h] <= s.p)
            else:
                mp.sc.add(mp.pi[s.zone, h] == s.p)
    for i, d in enumerate(seg_d):
        for h in hours:
            if d.qty[h] <= 0:
                continue
            c = _classify(xd[i, h])
            if c == 'acc':
                mp.sc.add(mp.pi[d.zone, h] <= d.p)
            elif c == 'rej':
                mp.sc.add(mp.pi[d.zone, h] >= d.p)
            else:
                mp.sc.add(mp.pi[d.zone, h] == d.p)
    mp.mup = Var(pairs, hours, domain=NonNegativeReals)   # multiplicateur de f <= NTC
    mp.mum = Var(pairs, hours, domain=NonNegativeReals)   # multiplicateur de f >= -NTC
    mp.lam = Var(hours, domain=NonNegativeReals)          # multiplicateur de la contrainte α
    alpha_cap = ALPHA * sum(ntc[l] for l in ALPHA_LINES) if alpha_active else None
    for h in hours:
        if not alpha_active or sum(fl[u, v, h] for u, v in ALPHA_LINES) < alpha_cap - F_TOL:
            mp.lam[h].fix(0)
    for u, v in pairs:
        cap = ntc[(u, v)]
        for h in hours:
            f = fl[u, v, h]
            if f < cap - F_TOL:
                mp.mup[u, v, h].fix(0)
            if f > -cap + F_TOL:
                mp.mum[u, v, h].fix(0)
            a = 1 if (alpha_active and (u, v) in ALPHA_LINES) else 0
            mp.sc.add(mp.pi[v, h] - mp.pi[u, h] - mp.mup[u, v, h] + mp.mum[u, v, h] - a * mp.lam[h] == 0)
    return mp


def _price_blocks(blocks, y, prices):
    """Statut de chaque bloc aux prix donnés : OK, PAB, PRB, inactive."""
    out = []
    for b, blk in enumerate(blocks):
        hb = blk.active_hours
        if not hb:
            out.append(dict(name=blk.name, zone=blk.zone, player=blk.player, side=blk.side,
                            quantity=blk.q, price=blk.p, hours=blk.hours, accepted=False,
                            avg_price=None, surplus=0.0, status='inactive'))
            continue
        avg = sum(prices[blk.zone, h] for h in hb) / len(hb)
        surplus = sum((prices[blk.zone, h] - blk.p) * blk.q for h in hb) if blk.side == 'S' \
            else sum((blk.p - prices[blk.zone, h]) * blk.q for h in hb)
        acc = bool(y.get(b, 0))
        if acc and surplus < -PRICE_TOL * blk.q * len(hb):
            status = 'PAB'
        elif (not acc) and surplus > PRICE_TOL * blk.q * len(hb):
            status = 'PRB'
        else:
            status = 'OK'
        out.append(dict(name=blk.name, zone=blk.zone, player=blk.player, side=blk.side,
                        quantity=blk.q, price=blk.p, hours=blk.hours, parent=blk.parent, group=blk.group,
                        accepted=acc, avg_price=round(avg, 2),
                        surplus=round(surplus if acc else 0.0, 1),
                        surplus_if_accepted=round(surplus, 1), status=status))
    return out


# ── Diagnostics de cohérence ──────────────────────────────────────
def _diagnostics(seg_s, seg_d, xs, xd, fl, prices, hours, ntc, pairs, alpha_active):
    pro = pao = 0
    max_viol = 0.0
    for i, s in enumerate(seg_s):
        for h in hours:
            if s.qty[h] <= 0:
                continue
            c, pi = _classify(xs[i, h]), prices[s.zone, h]
            if c == 'rej' and s.p < pi - PRICE_TOL:
                pro += 1; max_viol = max(max_viol, pi - s.p)
            if c in ('acc', 'part') and s.p > pi + PRICE_TOL:
                pao += 1; max_viol = max(max_viol, s.p - pi)
    for i, d in enumerate(seg_d):
        for h in hours:
            if d.qty[h] <= 0:
                continue
            c, pi = _classify(xd[i, h]), prices[d.zone, h]
            if c == 'rej' and d.p > pi + PRICE_TOL:
                pro += 1; max_viol = max(max_viol, d.p - pi)
            if c in ('acc', 'part') and d.p < pi - PRICE_TOL:
                pao += 1; max_viol = max(max_viol, pi - d.p)
    gaps = 0
    alpha_cap = ALPHA * sum(ntc[l] for l in ALPHA_LINES) if alpha_active else None
    for u, v in pairs:
        for h in hours:
            f = fl[u, v, h]
            if abs(f) < ntc[(u, v)] - F_TOL:
                if alpha_active and (u, v) in ALPHA_LINES and \
                        sum(fl[a, b, h] for a, b in ALPHA_LINES) >= alpha_cap - F_TOL:
                    continue
                dp = abs(prices[u, h] - prices[v, h])
                if dp > PRICE_TOL:
                    gaps += 1; max_viol = max(max_viol, dp)
    return dict(pro=pro, pao=pao, unsaturated_price_gaps=gaps, max_violation=round(max_viol, 3))


# ── Règle de partage des ex æquo ──────────────────────────────────
def _apply_tie_rule(seg_s, seg_d, xs, xd, hours, rule):
    """Répartit, entre offres de même zone, même sens, même heure et même prix, la quantité que le solveur
    a acceptée pour le groupe : 'prorata' (proportionnel aux quantités offertes), 'order' (dans l'ordre de
    soumission, premier servi), 'solver' (répartition laissée au solveur). Le total accepté du groupe est
    inchangé : ni le welfare, ni le volume, ni l'ensemble des prix admissibles ne bougent.
    Retourne le nombre de groupes (zone, heure, sens, prix) dont la répartition a été modifiée."""
    if rule == 'solver':
        return 0
    adjusted = 0
    for segs, x in ((seg_s, xs), (seg_d, xd)):
        for h in hours:
            groups = {}
            for i, s in enumerate(segs):
                if s.qty[h] > 0:
                    groups.setdefault((s.zone, s.p), []).append(i)
            for idx in groups.values():
                if len(idx) < 2:
                    continue
                total = sum(segs[i].qty[h] for i in idx)
                acc = sum(segs[i].qty[h] * x[i, h] for i in idx)
                if acc < X_TOL * total or acc > (1 - X_TOL) * total:
                    continue                       # groupe entièrement rejeté ou accepté : rien à partager
                if rule == 'prorata':
                    share = acc / total
                    new = {i: share for i in idx}
                else:                              # 'order' : premier soumis, premier servi
                    new, rem = {}, acc
                    for i in idx:
                        take = min(segs[i].qty[h], rem)
                        new[i] = take / segs[i].qty[h]
                        rem -= take
                if any(abs(new[i] - x[i, h]) > 1e-9 for i in idx):
                    adjusted += 1
                    for i in idx:
                        x[i, h] = new[i]
    return adjusted


# ── Minimum Income Condition ──────────────────────────────────────
@dataclass
class Mic:
    zone: str
    player: str
    actor: str
    fixed_term: float
    variable_term: float


def _build_mic(mic_rows):
    out = []
    for r in mic_rows:
        if r.get('zone') not in ZONES:
            raise ClearingError(f"Condition MIC de {r.get('actor', '?')} : zone inconnue.")
        out.append(Mic(r['zone'], r.get('player', ''), r['actor'],
                       float(r.get('fixed_term') or 0.0), float(r.get('variable_term') or 0.0)))
    return out


def _mic_check(mics, seg_s, blocks, xs, y, prices, hours, withdrawn):
    """Revenu de chaque acteur sous MIC aux prix finals, comparé à terme fixe + terme variable × volume.
    Un acteur dont rien n'est accepté satisfait trivialement sa condition (ordre inactif)."""
    results, to_withdraw = [], []
    for m in mics:
        key = (m.zone, m.player, m.actor)
        base = dict(zone=m.zone, player=m.player, actor=m.actor, fixed_term=m.fixed_term, variable_term=m.variable_term)
        if key in withdrawn:
            results.append(dict(base, accepted_mwh=0.0, income=0.0, required=round(m.fixed_term, 1), satisfied=False, withdrawn=True))
            continue
        acc = inc = 0.0
        for i, s in enumerate(seg_s):
            if (s.zone, s.player, s.actor) == key:
                for h in hours:
                    if s.qty[h] > 0:
                        q = s.qty[h] * xs[i, h]
                        acc += q
                        inc += prices[s.zone, h] * q
        for b, blk in enumerate(blocks):
            if blk.side == 'S' and (blk.zone, blk.player, blk.name) == key and y.get(b, 0):
                for h in blk.active_hours:
                    acc += blk.q
                    inc += prices[blk.zone, h] * blk.q
        req = m.fixed_term + m.variable_term * acc
        sat = acc <= 1e-6 or inc >= req - MIC_TOL
        results.append(dict(base, accepted_mwh=round(acc, 1), income=round(inc, 1), required=round(req, 1), satisfied=sat, withdrawn=False))
        if not sat:
            to_withdraw.append(key)
    return results, to_withdraw


# ── Séquence P1 → P1bis → P2 avec boucle PAB ──────────────────────
def _solve_sequence(seg_s, seg_d, blocks, parent_of, groups, hours, ntc, pairs, alpha_active,
                    solver, pricing, pab_rule, max_pab_iter, tie_rule, notes):
    fixed_y, iterations = {}, 0
    while True:
        iterations += 1
        m1 = _build_primal(seg_s, seg_d, blocks, parent_of, groups, hours, ntc, pairs,
                           objective='welfare', fixed_y=fixed_y)
        _solve(solver, m1, "P1 (welfare)")
        W_star = float(value(m1.welfare))
        xs, xd, fl, y = _extract(m1, seg_s, seg_d, blocks, hours, pairs)
        tie_break = 'none'

        # P1bis : volume maximal parmi les solutions de welfare optimal (ε = 0)
        if seg_s or seg_d:
            m2 = _build_primal(seg_s, seg_d, blocks, parent_of, groups, hours, ntc, pairs,
                               objective='volume', welfare_floor=W_star, fixed_y=dict(y))
            ok, status = _try_solve(solver, m2)
            if ok:
                xs, xd, fl, _ = _extract(m2, seg_s, seg_d, blocks, hours, pairs)
                tie_break = 'exact'
            else:
                notes.append(f"P1bis : départage par volume impossible ({status}) ; solution de P1 conservée.")
        tie_groups = _apply_tie_rule(seg_s, seg_d, xs, xd, hours, tie_rule)

        # P2
        mp = _build_pricing(seg_s, seg_d, xs, xd, fl, hours, ntc, pairs, alpha_active, pricing)
        ok, status = _try_solve(solver, mp)
        pricing_feasible = ok
        if not ok and tie_break == 'exact':
            xs, xd, fl, y = _extract(m1, seg_s, seg_d, blocks, hours, pairs)
            tie_break = 'fallback_p1'
            tie_groups = _apply_tie_rule(seg_s, seg_d, xs, xd, hours, tie_rule)
            mp = _build_pricing(seg_s, seg_d, xs, xd, fl, hours, ntc, pairs, alpha_active, pricing)
            ok, status = _try_solve(solver, mp)
            pricing_feasible = ok
            notes.append("P2 : la solution de P1bis n'admettait aucun prix admissible ; prix calculés sur la solution de P1.")
        if not ok:
            raise ClearingError(f"P2 (prix) : pas de solution ({status}). Vérifiez les offres (prix hors bornes, incohérences).")
        prices = {(z, h): float(value(mp.pi[z, h])) for z in ZONES for h in hours}

        # Blocs paradoxaux
        block_results = _price_blocks(blocks, y, prices) if blocks else []
        to_fix = {}
        for b, br in enumerate(block_results):
            if b in fixed_y:
                continue
            if br['status'] == 'PAB' and pab_rule in ('euphemia', 'l2'):
                to_fix[b] = 0
            elif br['status'] == 'PRB' and pab_rule == 'l2':
                to_fix[b] = 1
        if not to_fix or iterations > max_pab_iter:
            if to_fix:
                notes.append("Boucle PAB/PRB arrêtée au nombre maximal d'itérations.")
            break
        fixed_y.update(to_fix)
        notes.append("Itération %d : blocs fixés %s" % (iterations, {blocks[b].name: v for b, v in to_fix.items()}))
    return dict(xs=xs, xd=xd, fl=fl, y=y, prices=prices, block_results=block_results, W_star=W_star,
                iterations=iterations, fixed_y=fixed_y, tie_break=tie_break,
                pricing_feasible=pricing_feasible, tie_groups=tie_groups)


# ── Moteur principal ──────────────────────────────────────────────
def run_clearing(supply_rows=None, demand_rows=None, horizon=24, ntc_override=None, *,
                 block_rows=None, mic_rows=None, hours=None, fill_missing_zones=False,
                 pricing='complete', pab_rule='euphemia', tie_rule='prorata',
                 max_pab_iter=10, max_mic_iter=None):
    """
    Clearing complet P1 → P1bis → P2.

    supply_rows / demand_rows : lignes au format de la base (None pour les données de référence).
    block_rows   : ordres bloc, liés, exclusifs (format table block_orders) ; None = aucun.
    mic_rows     : conditions de revenu minimum (zone, player, actor, fixed_term, variable_term) ; None = aucune.
    horizon      : 24 (jour complet) ou 1 ; ignoré si `hours` est fourni.
    hours        : liste d'heures simulées (ex. [19]) ; par défaut range(horizon).
    ntc_override : {(u, v): MW} ; sinon NTC de la base (si définies), sinon valeurs par défaut.
    fill_missing_zones : complète les zones sans aucune soumission avec les données de référence.
    pricing      : 'complete' (KKT complètes, v2) ou 'l2' (contraintes (8)-(12) du Livrable 2).
    pab_rule     : 'euphemia' (rejet itératif des PAB, PRB tolérés), 'l2' (PAB fixés à 0 et
                   PRB fixés à 1, Livrable 2 §3.3) ou 'none' (détection seule).
    tie_rule     : partage des offres au même prix : 'prorata' (défaut), 'order', 'solver'.
    Retourne dict : prices, flows, dispatch, welfare, volume, summary.
    """
    t_total = time.time()
    if pricing not in PRICING_MODES:
        raise ClearingError(f"Mode de prix inconnu : {pricing}")
    if pab_rule not in PAB_RULES:
        raise ClearingError(f"Règle PAB inconnue : {pab_rule}")
    if tie_rule not in TIE_RULES:
        raise ClearingError(f"Règle de partage inconnue : {tie_rule}")
    notes = []

    # ── Heures simulées ───────────────────────────────────────────
    if hours is None:
        hours = list(range(int(horizon)))
    hours = [int(h) for h in hours]
    if not hours or any(h < 0 or h > 23 for h in hours):
        raise ClearingError("Les heures simulées doivent être comprises entre 0 et 23.")

    # ── Données ───────────────────────────────────────────────────
    if supply_rows is None and demand_rows is None:
        supply_rows, demand_rows = default_rows()
        notes.append("Données de référence utilisées pour les 14 zones.")
    else:
        supply_rows = list(supply_rows or [])
        demand_rows = list(demand_rows or [])
        if fill_missing_zones:
            covered = {r['zone'] for r in supply_rows} | {r['zone'] for r in demand_rows} \
                    | {r['zone'] for r in (block_rows or [])}
            missing = [z for z in ZONES if z not in covered]
            if missing:
                ds, dd = default_rows(zones=missing)
                supply_rows += ds
                demand_rows += dd
                notes.append(f"Zones complétées par les données de référence : {', '.join(missing)}.")
    block_rows = list(block_rows or [])
    validate_inputs(supply_rows, demand_rows, block_rows)

    seg_s_all, seg_d = _build_segments(supply_rows, demand_rows, hours)
    blocks_all = _build_blocks(block_rows, hours)
    mics = _build_mic(mic_rows or [])
    if max_mic_iter is None:
        max_mic_iter = len(mics) + 1

    # ── NTC : override > base > défaut ────────────────────────────
    ntc = dict(NTC)
    if ntc_override:
        ntc.update({tuple(k): float(v) for k, v in ntc_override.items()})
    else:
        try:
            from engine.db import get_ntc
            db_ntc = get_ntc()
            if db_ntc:
                ntc.update(db_ntc)
                changed = [f"{u}->{v}" for (u, v), mw in db_ntc.items() if abs(mw - NTC.get((u, v), mw)) > 1e-9]
                if changed:
                    notes.append("NTC modifiées par l'administrateur sur : " + ", ".join(changed) + ".")
        except Exception as e:          # base absente : valeurs par défaut
            logger.debug("NTC par défaut (%s)", e)
    pairs = list(ntc.keys())
    alpha_active = all(l in ntc for l in ALPHA_LINES)

    solver, solver_name = _get_solver()
    logger.info("Solveur %s | %d segments vente, %d segments achat, %d blocs, %d MIC, %d heures",
                solver_name, len(seg_s_all), len(seg_d), len(blocks_all), len(mics), len(hours))

    # ── Boucle MIC autour de la séquence P1 → P1bis → P2 ──────────
    withdrawn = set()
    mic_iter = 0
    while True:
        mic_iter += 1
        seg_s = [s for s in seg_s_all if (s.zone, s.player, s.actor) not in withdrawn]
        # Blocs retirés : ceux de l'acteur retiré, puis leurs enfants (un enfant sans parent ne peut être accepté)
        gone = {(b.zone, b.player, b.name) for b in blocks_all if b.side == 'S' and (b.zone, b.player, b.name) in withdrawn}
        changed = True
        while changed:
            changed = False
            for b in blocks_all:
                if (b.zone, b.player, b.name) not in gone and b.parent and (b.zone, b.player, b.parent) in gone:
                    gone.add((b.zone, b.player, b.name)); changed = True
        blocks = [b for b in blocks_all if (b.zone, b.player, b.name) not in gone]
        parent_of, groups = _resolve_links(blocks, notes if mic_iter == 1 else [])
        sol = _solve_sequence(seg_s, seg_d, blocks, parent_of, groups, hours, ntc, pairs, alpha_active,
                              solver, pricing, pab_rule, max_pab_iter, tie_rule, notes)
        mic_results, to_withdraw = _mic_check(mics, seg_s, blocks, sol['xs'], sol['y'], sol['prices'], hours, withdrawn)
        if not to_withdraw or mic_iter > max_mic_iter:
            if to_withdraw:
                notes.append("Boucle MIC arrêtée au nombre maximal d'itérations.")
            break
        withdrawn |= set(to_withdraw)
        notes.append("MIC non satisfaite, offres retirées : " + ", ".join(f"{a} ({z})" for z, _, a in to_withdraw) + ".")

    xs, xd, fl, y, prices = sol['xs'], sol['xd'], sol['fl'], sol['y'], sol['prices']
    block_results = sol['block_results']
    S, D, B = range(len(seg_s)), range(len(seg_d)), range(len(blocks))
    vol = sum(seg_s[s].qty[h] * xs[s, h] for s in S for h in hours if seg_s[s].qty[h] > 0) \
        + sum(blocks[b].q * len(blocks[b].active_hours) * y.get(b, 0) for b in B if blocks[b].side == 'S')

    # ── Résultats ─────────────────────────────────────────────────
    prices_out = {z: {str(h): round(prices[z, h], 2) for h in hours} for z in ZONES}
    flows_out = {f"{u}->{v}": {str(h): round(fl[u, v, h], 1) for h in hours} for u, v in pairs}

    n = len(hours)
    idx = {h: i for i, h in enumerate(hours)}
    dispatch = {k: [0.0] * n for k in ['solar', 'hydro', 'baseload', 'peaker', 'flat', 'custom', 'block']}
    demand_accepted = [0.0] * n
    for s in S:
        for h in hours:
            if seg_s[s].qty[h] > 0:
                dispatch[seg_s[s].profile][idx[h]] += seg_s[s].qty[h] * xs[s, h]
    for d in D:
        for h in hours:
            if seg_d[d].qty[h] > 0:
                demand_accepted[idx[h]] += seg_d[d].qty[h] * xd[d, h]
    for b in B:
        if y.get(b, 0):
            for h in blocks[b].active_hours:
                if blocks[b].side == 'S':
                    dispatch['block'][idx[h]] += blocks[b].q
                else:
                    demand_accepted[idx[h]] += blocks[b].q
    dispatch['demand'] = demand_accepted

    # Résultats par acteur (vue trader)
    actors = {}
    def _acc(key, **kw):
        a = actors.setdefault(key, dict(zone=key[0], player=key[1], actor=key[2], side=key[3],
                                        offered_mwh=0.0, accepted_mwh=0.0, money=0.0, value=0.0,
                                        rejected=[], status='ok'))
        for k2, v2 in kw.items():
            if k2 == 'rejected':
                a['rejected'].append(v2)
            elif k2 == 'status':
                a['status'] = v2
            else:
                a[k2] += v2
    for s in S:
        key = (seg_s[s].zone, seg_s[s].player, seg_s[s].actor, 'S')
        for h in hours:
            Q = seg_s[s].qty[h]
            if Q <= 0:
                continue
            q = Q * xs[s, h]
            _acc(key, offered_mwh=Q, accepted_mwh=q, money=prices[seg_s[s].zone, h] * q, value=seg_s[s].p * q)
        if all(_classify(xs[s, h]) == 'rej' for h in hours if seg_s[s].qty[h] > 0):
            _acc(key, rejected=dict(segment=seg_s[s].k, quantity=seg_s[s].q, price=seg_s[s].p))
    for s in seg_s_all:                       # acteurs retirés par la MIC
        key = (s.zone, s.player, s.actor, 'S')
        if (s.zone, s.player, s.actor) in withdrawn:
            _acc(key, offered_mwh=sum(s.qty[h] for h in hours), status='withdrawn_mic',
                 rejected=dict(segment=s.k, quantity=s.q, price=s.p))
    for d in D:
        key = (seg_d[d].zone, seg_d[d].player, seg_d[d].actor, 'D')
        for h in hours:
            Q = seg_d[d].qty[h]
            if Q <= 0:
                continue
            q = Q * xd[d, h]
            _acc(key, offered_mwh=Q, accepted_mwh=q, money=prices[seg_d[d].zone, h] * q, value=seg_d[d].p * q)
        if all(_classify(xd[d, h]) == 'rej' for h in hours if seg_d[d].qty[h] > 0):
            _acc(key, rejected=dict(segment=seg_d[d].k, quantity=seg_d[d].q, price=seg_d[d].p))
    for b in B:
        blk = blocks[b]
        key = (blk.zone, blk.player, blk.name, blk.side)
        nh = len(blk.active_hours)
        if nh == 0:
            continue
        _acc(key, offered_mwh=blk.q * nh)
        if y.get(b, 0):
            _acc(key, accepted_mwh=blk.q * nh, money=sum(prices[blk.zone, h] for h in blk.active_hours) * blk.q,
                 value=blk.p * blk.q * nh)
        else:
            _acc(key, rejected=dict(segment='bloc', quantity=blk.q, price=blk.p))
    for blk in blocks_all:
        if (blk.zone, blk.player, blk.name) in gone and blk.side == 'S':
            _acc((blk.zone, blk.player, blk.name, 'S'), offered_mwh=blk.q * len(blk.active_hours),
                 status='withdrawn_mic', rejected=dict(segment='bloc', quantity=blk.q, price=blk.p))
    actor_list = []
    for a in actors.values():
        a['surplus'] = (a['money'] - a['value']) if a['side'] == 'S' else (a['value'] - a['money'])
        a['avg_price'] = (a['money'] / a['accepted_mwh']) if a['accepted_mwh'] > 1e-9 else None
        a['acceptance_pct'] = (100 * a['accepted_mwh'] / a['offered_mwh']) if a['offered_mwh'] > 0 else 0.0
        for k2 in ('offered_mwh', 'accepted_mwh', 'money', 'value', 'surplus', 'acceptance_pct'):
            a[k2] = round(a[k2], 1)
        if a['avg_price'] is not None:
            a['avg_price'] = round(a['avg_price'], 2)
        actor_list.append(a)
    actor_list.sort(key=lambda a: (a['zone'], a['player'], a['side'], a['actor']))

    # Décomposition par zone et rente de congestion
    zones_out = {}
    for z in ZONES:
        gen = sum(seg_s[s].qty[h] * xs[s, h] for s in S for h in hours if seg_s[s].zone == z and seg_s[s].qty[h] > 0) \
            + sum(blocks[b].q * len(blocks[b].active_hours) * y.get(b, 0) for b in B if blocks[b].zone == z and blocks[b].side == 'S')
        load = sum(seg_d[d].qty[h] * xd[d, h] for d in D for h in hours if seg_d[d].zone == z and seg_d[d].qty[h] > 0) \
            + sum(blocks[b].q * len(blocks[b].active_hours) * y.get(b, 0) for b in B if blocks[b].zone == z and blocks[b].side == 'D')
        ps = sum((prices[z, h] - seg_s[s].p) * seg_s[s].qty[h] * xs[s, h] for s in S for h in hours if seg_s[s].zone == z and seg_s[s].qty[h] > 0) \
           + sum(sum(prices[z, h] - blocks[b].p for h in blocks[b].active_hours) * blocks[b].q * y.get(b, 0) for b in B if blocks[b].zone == z and blocks[b].side == 'S')
        cs = sum((seg_d[d].p - prices[z, h]) * seg_d[d].qty[h] * xd[d, h] for d in D for h in hours if seg_d[d].zone == z and seg_d[d].qty[h] > 0) \
           + sum(sum(blocks[b].p - prices[z, h] for h in blocks[b].active_hours) * blocks[b].q * y.get(b, 0) for b in B if blocks[b].zone == z and blocks[b].side == 'D')
        zones_out[z] = dict(generation_mwh=round(gen, 1), load_mwh=round(load, 1), net_position=round(gen - load, 1),
                            producer_surplus=round(ps, 1), consumer_surplus=round(cs, 1),
                            avg_price=round(sum(prices[z, h] for h in hours) / n, 2),
                            no_trade_hours=[h for h in hours if
                                            all(seg_s[s].zone != z or seg_s[s].qty[h] <= 0 or xs[s, h] < X_TOL for s in S) and
                                            all(seg_d[d].zone != z or seg_d[d].qty[h] <= 0 or xd[d, h] < X_TOL for d in D) and
                                            not any(blocks[b].zone == z and h in blocks[b].active_hours and y.get(b, 0) for b in B)])
    lines_out = {}
    for u, v in pairs:
        rent = sum(fl[u, v, h] * (prices[v, h] - prices[u, h]) for h in hours)
        sat = sum(1 for h in hours if abs(fl[u, v, h]) >= ntc[(u, v)] - F_TOL)
        lines_out[f"{u}->{v}"] = dict(ntc=ntc[(u, v)], congestion_rent=round(rent, 1), saturated_hours=sat,
                                      avg_flow=round(sum(fl[u, v, h] for h in hours) / n, 1))
    welfare_hourly = [
        sum(seg_d[d].p * seg_d[d].qty[h] * xd[d, h] for d in D if seg_d[d].qty[h] > 0)
        - sum(seg_s[s].p * seg_s[s].qty[h] * xs[s, h] for s in S if seg_s[s].qty[h] > 0)
        + sum((blocks[b].p if blocks[b].side == 'D' else -blocks[b].p) * blocks[b].q * y.get(b, 0)
              for b in B if h in blocks[b].active_hours)
        for h in hours
    ]
    W_final = sum(welfare_hourly)
    cs_tot = sum(zz['consumer_surplus'] for zz in zones_out.values())
    ps_tot = sum(zz['producer_surplus'] for zz in zones_out.values())
    cr_tot = sum(l['congestion_rent'] for l in lines_out.values())

    diag = _diagnostics(seg_s, seg_d, xs, xd, fl, prices, hours, ntc, pairs, alpha_active)
    diag.update(dict(pricing_mode=pricing, pricing_feasible=sol['pricing_feasible'], tie_break=sol['tie_break'],
                     tie_rule=tie_rule, tie_groups_adjusted=sol['tie_groups'],
                     pab_iterations=sol['iterations'], blocks_fixed={blocks[b].name: v for b, v in sol['fixed_y'].items()},
                     prb=[br['name'] for br in block_results if br['status'] == 'PRB'],
                     pab=[br['name'] for br in block_results if br['status'] == 'PAB'],
                     mic_iterations=mic_iter, mic_withdrawn=[f"{a} ({z})" for z, _, a in sorted(withdrawn)],
                     welfare_identity_gap=round(W_final - (cs_tot + ps_tot + cr_tot), 1),
                     notes=notes))

    summary = {
        'welfare':         round(W_final, 0),
        'volume':          round(vol, 0),
        'elapsed':         round(time.time() - t_total, 2),
        'solver':          solver_name,
        'horizon':         len(hours),
        'hours':           hours,
        'n_supply':        len(seg_s_all),
        'n_demand':        len(seg_d),
        'n_blocks':        len(blocks_all),
        'n_mic':           len(mics),
        'n_withdrawn':     len(withdrawn),
        'net_pos':         {z: zones_out[z]['net_position'] for z in ZONES},
        'demand_accepted': demand_accepted,
        'welfare_hourly':  welfare_hourly,
        'consumer_surplus': round(cs_tot, 1),
        'producer_surplus': round(ps_tot, 1),
        'congestion_rent':  round(cr_tot, 1),
        'zones':           zones_out,
        'lines':           lines_out,
        'blocks':          block_results,
        'mic':             mic_results,
        'actors':          actor_list,
        'rules':           dict(pricing=pricing, pab_rule=pab_rule, tie_rule=tie_rule,
                                tie_break='volume max, welfare exact', x_tol=X_TOL, f_tol=F_TOL, mic_tol=MIC_TOL,
                                price_bounds=[P_MIN, P_MAX], alpha=ALPHA,
                                ntc=dict((f"{u}->{v}", ntc[(u, v)]) for u, v in pairs)),
        'diagnostics':     diag,
    }
    logger.info("Clearing terminé en %.2fs | W=%.0f | Vol=%.0f MWh | %s",
                summary['elapsed'], W_final, vol, diag)
    return {
        'prices':   prices_out,
        'flows':    flows_out,
        'dispatch': dispatch,
        'welfare':  W_final,
        'volume':   vol,
        'summary':  summary,
    }
