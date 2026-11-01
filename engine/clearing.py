"""
WAPP Day-Ahead Market Clearing Engine — v2 (October 2026)

Sequential decomposition of Deliverable 2 (8 March 2026):
    P1    : welfare maximisation (LP; MILP when block orders are present)
    P1bis : volume maximisation among welfare-optimal solutions (LP, tie-break)
    P2    : zonal prices = admissible prices closest to the midpoints of the intervals,
            sum of squared deviations (QP, unique prices)

Changes in v2 compared with the Deliverable 3 engine (details in CHANGELOG.md and docs/MARKET_RULES.md):
    - "Complete" P2: the set of admissible prices is described by the full KKT conditions
      (rejected orders, price equality across unsaturated lines, multiplier of the α constraint).
      Mode 'l2' keeps constraints (8)-(12) of Deliverable 2 for comparison.
    - Exact P1bis (ε = 0) instead of ε = 0.01; documented fallback if the solver cannot follow.
      With blocks, the welfare floor W* of P1bis is the optimum of the linear program with the
      blocks fixed, not the value of the MILP solution (which stops at a relative gap MIP_GAP).
    - P2 minimises the sum of squared deviations from the reference prices (quadratic program,
      unique prices); it needs Gurobi or HiGHS through Pyomo >= 6.9.3 (interface 'highs').
    - Block, linked and exclusive orders (MILP) ported from the notebook wapp_market_clearing_final1.ipynb;
      rejection loop for paradoxically accepted blocks (EUPHEMIA rule); PRBs reported, assessed for
      the whole family of linked blocks and for the whole exclusive group.
    - Configurable NTC, configurable simulated hours, missing zones filled with reference data,
      input validation.
    - Solver status checked at every step (ClearingError) and consistency diagnostics.
    - Explicit sharing rule for equal-price orders (pro rata by default) after P1bis.
    - Minimum Income Condition (income ≥ fixed term + variable term × volume) with iterative withdrawal.
"""

#===================================================================================================
# FILE MAP
# BLOCK 0  Imports and public interface
# BLOCK 1  Parameters and reference data
#          1.1 Regulatory and numerical parameters   1.2 Network: zones and lines
#          1.3 Hourly profiles                        1.4 Reference data (Deliverable 2)
# BLOCK 2  Data structures and helpers
#          2.1 Actor identification and errors        2.2 Seg and Block records
#          2.3 Profiles and loading of the reference data
# BLOCK 3  Order preparation
#          3.1 Input validation   3.2 Segments and blocks   3.3 Links between blocks
# BLOCK 4  Solver
#          4.1 Choice of the solver   4.2 Safe solving
# BLOCK 5  The optimisation problems P1, P1bis and P2
#          5.1 P1 and P1bis (primal model)   5.2 P2: status of the orders and reference prices
#          5.3 P2: quadratic program of the prices
# BLOCK 6  Checks and rules applied around the prices
#          6.1 Paradoxical blocks (PAB / PRB, families and exclusive groups)   6.2 Consistency diagnostics
#          6.3 Sharing of equal-price orders (pro rata)
# BLOCK 7  Minimum income condition (MIC)
#          7.1 Reading and validation of the MICs   7.2 Check of the MICs at final prices
# BLOCK 8  Complete algorithm: P1 → P1bis → P2 and the paradoxical-block loop
# BLOCK 9  Entry point run_clearing
#          9.1 Rule checks         9.2 Simulated hours       9.3 Data: choice of the orders
#          9.4 Validation and construction                 9.5 Line capacities (NTC)
#          9.6 MIC loop            9.7 MIC reinsertion       9.8 Final solution and volume
#          9.9 Prices, flows and generation   9.10 Results per actor   9.11 Results per zone and line, welfare
#          9.12 Diagnostics        9.13 Summary and output
#===================================================================================================

#===================================================================================================
# BLOCK 0 — IMPORTS AND PUBLIC INTERFACE
#---------------------------------------------------------------------------------------------------
# Libraries used (Pyomo writes the optimisation models) and the __all__ list of what the other
# files (API, CLI, tests) may import.
#===================================================================================================

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


#===================================================================================================
# BLOCK 1 — PARAMETERS AND REFERENCE DATA
#---------------------------------------------------------------------------------------------------
# Every constant of the engine: tolerances, price bounds, network, hourly profiles and the test
# set of Deliverable 2. No computation here.
#===================================================================================================

#---------------------------------------------------------------------------------------------------
# 1.1  Regulatory and numerical parameters
#   Price bounds, factor α of Burkina Faso, tolerances (ε_x, ε_f, ε_π, ε_m), available rules,
#   segment limit and optimality gap of the MILP.
#---------------------------------------------------------------------------------------------------
# ── Regulatory and numerical parameters ───────────────────────────
P_MIN, P_MAX = 0, 500      # price bounds (Deliverable 2, table 2)
ALPHA = 0.7                # CIV/GHA/BFA interdependence factor (constraint C4)
X_TOL = 1e-4               # fraction: x < X_TOL = rejected, x > 1 - X_TOL = fully accepted
F_TOL = 1e-3               # MW: a line is saturated when |f| >= NTC - F_TOL
PRICE_TOL = 0.5            # currency/MWh: tolerance of the consistency diagnostics
PRICING_MODES = ('complete', 'l2')
PAB_RULES = ('euphemia', 'l2', 'none')
TIE_RULES = ('prorata', 'order', 'solver')   # sharing of equal-price orders
MIC_TOL = 0.5              # currency unit: tolerance of the minimum income condition
MAX_SEGMENTS = 4           # maximum number of segments per actor and per side (sell / buy)
MIP_GAP = 1e-6             # relative optimality gap of the MILP, the same for every solver

#---------------------------------------------------------------------------------------------------
# 1.2  Network: zones and lines
#   The 14 zones, the 15 lines with their default NTC (those of the test set) and the two lines
#   of the α constraint (into Burkina Faso).
#---------------------------------------------------------------------------------------------------
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

#---------------------------------------------------------------------------------------------------
# 1.3  Hourly profiles
#   Availability profiles of the supply (solar, hydro, baseload, peaker, flat) and the common
#   load profile LOAD_WA.
#---------------------------------------------------------------------------------------------------
# ── Hourly profiles (Deliverable 2, tables 12 and 13) ─────────────
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

#---------------------------------------------------------------------------------------------------
# 1.4  Reference data (Deliverable 2, step 3)
#   Synthetic test set: 28 sellers (64 segments) and 15 buyers (44 segments). This is the case
#   run by "cli --reference".
#---------------------------------------------------------------------------------------------------
# ── Reference data (notebook / Deliverable 2, step 3) ─────────────
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


#===================================================================================================
# BLOCK 2 — DATA STRUCTURES AND HELPERS
#---------------------------------------------------------------------------------------------------
# The records that describe the orders inside the engine, and a few small helpers.
#===================================================================================================

#---------------------------------------------------------------------------------------------------
# 2.1  Actor identification and errors
#   Label of the reference orders, normalisation of actor names and the ClearingError type.
#---------------------------------------------------------------------------------------------------
REFERENCE_PLAYER = 'Référence'

def _name_key(name):
    """Normalised form of an actor or organisation name for matching (lower case, no accents or
    punctuation, generic words such as "demand", "gen", "réseau" removed)."""
    import unicodedata, re
    s = unicodedata.normalize('NFKD', str(name)).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    words = [w for w in s.split() if w not in ('demand', 'gen', 'reseau', 'network', 'distribution', 'thermal', 'hydro', 'solar')]
    return ' '.join(words) or s.strip()

class ClearingError(Exception):
    """Clearing error with a message readable by the administrator."""

#---------------------------------------------------------------------------------------------------
# 2.2  Seg and Block records
#   Seg: a segment of a simple order (sell or buy) with its effective hourly quantities.
#   Block: a block order with its hours, its parent and its exclusive group.
#---------------------------------------------------------------------------------------------------
# ── Internal structures ───────────────────────────────────────────
@dataclass
class Seg:
    actor: str
    zone: str
    k: int                    # segment index
    q: float                  # power (MW)
    p: float                  # price
    profile: str              # profile name
    qty: dict                 # {hour: effective quantity}
    player: str = ''          # participant who submitted it
    side: str = 'S'           # 'S' sell, 'D' buy

@dataclass
class Block:
    name: str
    zone: str
    side: str                 # 'S' sell, 'D' buy
    q: float
    p: float
    hours: list
    parent: Optional[str] = None
    group: Optional[str] = None
    player: str = ''
    active_hours: list = field(default_factory=list)

#---------------------------------------------------------------------------------------------------
# 2.3  Profiles and loading of the reference data
#   Conversion profile name ↔ vector of 24 values, and the test set as order rows
#   (default_rows).
#---------------------------------------------------------------------------------------------------
def _profile_name(arr):
    """Profile name for a 24-value vector (peaker takes precedence over flat, which are identical)."""
    t = tuple(arr)
    for name in ('solar', 'hydro', 'baseload', 'peaker'):
        if tuple(PROF[name]) == t:
            return name
    return 'custom'

def _profile_array(prof):
    """Accepts a profile name or a 24-value vector. Returns (vector, name)."""
    if prof is None:
        return PROF['baseload'], 'baseload'
    if isinstance(prof, str):
        if prof in PROF:
            return PROF[prof], prof
        raise ClearingError(f"Unknown hourly profile: '{prof}' (expected: {', '.join(PROF)}).")
    arr = [float(v) for v in prof]
    if len(arr) != 24:
        raise ClearingError("A custom hourly profile must contain 24 values.")
    return arr, _profile_name(arr)

def default_rows(zones=None):
    """Reference data in the database row format (sell and buy orders)."""
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


#===================================================================================================
# BLOCK 3 — ORDER PREPARATION
#---------------------------------------------------------------------------------------------------
# Before any optimisation: check of the submitted orders, hourly quantities and resolution of
# the links between blocks.
#===================================================================================================

#---------------------------------------------------------------------------------------------------
# 3.1  Input validation
#   Zones, quantities, price bounds, block hours and the limit of 4 segments per actor and per
#   side.
#---------------------------------------------------------------------------------------------------
# ── Input validation ──────────────────────────────────────────────
def validate_inputs(supply_rows, demand_rows, block_rows):
    """Raises ClearingError with a precise message when an input is out of specification."""
    for kind, rows in (('sell', supply_rows), ('buy', demand_rows)):
        for r in rows:
            who = f"{r.get('actor', '?')} ({r.get('zone', '?')})"
            if r.get('zone') not in ZONES:
                raise ClearingError(f"{kind.capitalize()} order {who}: unknown zone.")
            q, p = float(r.get('quantity', 0)), float(r.get('price', 0))
            if q < 0:
                raise ClearingError(f"{kind.capitalize()} order {who}: negative quantity.")
            if not (P_MIN <= p <= P_MAX):
                raise ClearingError(f"{kind.capitalize()} order {who}: price {p:g} outside the bounds [{P_MIN}, {P_MAX}].")
        # At most MAX_SEGMENTS segments per actor (same zone, participant and actor name) and per side
        n_seg = {}
        for r in rows:
            key = (r.get('zone'), r.get('player', ''), r.get('actor', '?'))
            n_seg[key] = n_seg.get(key, 0) + 1
            if n_seg[key] > MAX_SEGMENTS:
                raise ClearingError(f"{kind.capitalize()} order {r.get('actor', '?')} ({r.get('zone', '?')}): "
                                    f"more than {MAX_SEGMENTS} segments; an actor submits at most {MAX_SEGMENTS} segments per side.")
    for r in block_rows:
        who = f"{r.get('name', '?')} ({r.get('zone', '?')})"
        if r.get('zone') not in ZONES:
            raise ClearingError(f"Block {who}: unknown zone.")
        if r.get('side') not in ('S', 'D'):
            raise ClearingError(f"Block {who}: side must be 'S' (sell) or 'D' (buy).")
        q, p = float(r.get('quantity', 0)), float(r.get('price', 0))
        if q < 0:
            raise ClearingError(f"Block {who}: negative quantity.")
        if not (P_MIN <= p <= P_MAX):
            raise ClearingError(f"Block {who}: price {p:g} outside the bounds [{P_MIN}, {P_MAX}].")
        h0, h1 = int(r.get('h_start', 0)), int(r.get('h_end', 23))
        if not (0 <= h0 <= 23 and 0 <= h1 <= 23 and h0 <= h1):
            raise ClearingError(f"Block {who}: invalid hour range ({h0}-{h1}).")


#---------------------------------------------------------------------------------------------------
# 3.2  Segments and blocks
#   Hourly quantity = power × profile (supply) or × load profile (demand); active hours of
#   each block within the horizon.
#---------------------------------------------------------------------------------------------------
# ── Segment and block construction ────────────────────────────────
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

#---------------------------------------------------------------------------------------------------
# 3.3  Links between blocks
#   Parent-child pairs (one level, several children allowed) and exclusive groups; invalid
#   links raise an error.
#---------------------------------------------------------------------------------------------------
def _resolve_links(blocks, notes):
    """Links the blocks of one actor in one zone: parent-child pairs and exclusive groups.

    Rules (a ClearingError is raised otherwise):
      - two blocks of the same actor in the same zone cannot have the same name;
      - the parent of a block must exist among the blocks of the same actor in the same zone;
      - a block cannot be its own parent;
      - a parent may have several children, but a child cannot itself be a parent
        (no grandparent -> parent -> child chains, hence no cycles);
      - an exclusive group must contain at least two blocks.
    """
    # 1. Directory of the blocks; duplicate names are refused
    index = {}
    for i, b in enumerate(blocks):
        key = (b.zone, b.player, b.name)
        if key in index:
            raise ClearingError(f"Block '{b.name}' ({b.zone}): two blocks of the same trader have this name; "
                                "give each block a distinct name.")
        index[key] = i

    # 2. Child -> parent links: the parent must exist and cannot be the block itself
    parent_of = {}
    for i, b in enumerate(blocks):
        if b.parent:
            j = index.get((b.zone, b.player, b.parent))
            if j is None:
                raise ClearingError(f"Block '{b.name}' ({b.zone}): parent '{b.parent}' not found among the blocks "
                                    "of the same trader in the same zone.")
            if j == i:
                raise ClearingError(f"Block '{b.name}' ({b.zone}): a block cannot be its own parent.")
            parent_of[i] = j

    # 3. No chains: the parent of a block cannot itself be a child (which also excludes cycles)
    for i, j in parent_of.items():
        if j in parent_of:
            raise ClearingError(f"Block '{blocks[i].name}' ({blocks[i].zone}): its parent '{blocks[j].name}' is itself "
                                "the child of another block; only one level of links is allowed (no chains).")

    # 4. Exclusive groups: at least two blocks
    groups = {}
    for i, b in enumerate(blocks):
        if b.group:
            groups.setdefault((b.zone, b.player, b.group), []).append(i)
    for (z, _, g), members in groups.items():
        if len(members) < 2:
            raise ClearingError(f"Exclusive group '{g}' ({z}): an exclusive group must contain at least two blocks.")
    return parent_of, list(groups.values())


#===================================================================================================
# BLOCK 4 — SOLVER
#---------------------------------------------------------------------------------------------------
# Choice of an available solver and safe solving of the models: a failure is detected and
# reported instead of producing meaningless values.
#===================================================================================================

#---------------------------------------------------------------------------------------------------
# 4.1  Choice of the solver
#   Gurobi, then HiGHS, GLPK, CBC; the first one available is used, with the same optimality
#   gap MIP_GAP.
#---------------------------------------------------------------------------------------------------
# ── Solver ────────────────────────────────────────────────────────
def _get_solver():
    """Gurobi → HiGHS (appsi) → GLPK → CBC. Returns (solver, name)."""
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
                # The same optimality gap MIP_GAP for every solver (each has its own option name)
                try:
                    if name == 'gurobi':
                        s.options['MIPGap'] = MIP_GAP
                    elif name == 'appsi_highs':
                        s.options['mip_rel_gap'] = MIP_GAP
                    elif name == 'glpk':
                        s.options['mipgap'] = MIP_GAP
                    elif name == 'cbc':
                        s.options['ratio'] = MIP_GAP
                except Exception:
                    pass
                return s, name
        except Exception:
            pass
    raise ClearingError("No solver available. Install HiGHS: pip install highspy")


def _get_qp_solver():
    """Solver of the quadratic P2: Gurobi, else HiGHS through the 'highs' interface of Pyomo (>= 6.9.3).
    The 'appsi_highs' interface used for P1 and P1bis does not accept a quadratic objective, nor do
    GLPK and CBC. Returns (solver, name), or (None, None) when none is suitable."""
    for name in ('gurobi', 'highs'):
        try:
            s = SolverFactory(name)
            if s.available():
                return s, name
        except Exception:
            pass
    return None, None


#---------------------------------------------------------------------------------------------------
# 4.2  Safe solving
#   _try_solve: returns success / failure without stopping the computation (for the steps that
#   have a fallback). _solve: stops with an error on failure.
#---------------------------------------------------------------------------------------------------
_OK = (_TC.optimal, _TC.globallyOptimal, _TC.locallyOptimal)


def _try_solve(solver, model):
    """Solves without loading the solution; loads it when optimal. Returns (ok, status)."""
    try:
        res = solver.solve(model, load_solutions=False, tee=False)
    except Exception as e:                       # internal solver error
        return False, f"solver error: {e}"
    tc = res.solver.termination_condition
    if tc in _OK:
        model.solutions.load_from(res)
        return True, str(tc)
    return False, str(tc)


def _solve(solver, model, label):
    ok, status = _try_solve(solver, model)
    if not ok:
        raise ClearingError(f"{label}: no optimal solution ({status}).")
    return status


#===================================================================================================
# BLOCK 5 — THE OPTIMISATION PROBLEMS P1, P1bis AND P2
#---------------------------------------------------------------------------------------------------
# The mathematical core of the working paper (Section 2.7). P1 maximises the welfare, P1bis
# maximises the volume without losing welfare, P2 chooses the admissible prices closest to the
# reference prices.
#===================================================================================================

#---------------------------------------------------------------------------------------------------
# 5.1  P1 and P1bis (primal model)
#   Variables (acceptance ratios, flows, block binaries), welfare, balance of each zone,
#   α constraint, links and exclusive groups; objective welfare (P1) or volume with W ≥ W*
#   (P1bis). _extract reads the solution.
#---------------------------------------------------------------------------------------------------
# ── Primal model (P1 / P1bis) ─────────────────────────────────────
def _build_primal(seg_s, seg_d, blocks, parent_of, groups, hours, ntc, pairs,
                  objective='welfare', welfare_floor=None, fixed_y=None, cuts=None):
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
        # Family cuts (rule 'euphemia'): each cut forbids the one configuration (parent + children)
        # that produced a PAB; every other configuration remains possible.
        m.cuts = ConstraintList()
        for config in (cuts or []):
            m.cuts.add(sum(1 - m.yb[k] for k, v in config if v == 1)
                       + sum(m.yb[k] for k, v in config if v == 0) >= 1)

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


#---------------------------------------------------------------------------------------------------
# 5.2  P2: status of the orders and reference prices
#   Accepted / partial / rejected classification with ε_x, and the price interval allowed by the
#   orders of each zone; its midpoint is the reference price (eq. 13 of the paper).
#---------------------------------------------------------------------------------------------------
# ── P2: zonal prices ──────────────────────────────────────────────
def _classify(x):
    if x > 1 - X_TOL:
        return 'acc'
    if x < X_TOL:
        return 'rej'
    return 'part'

def _reference_prices(seg_s, seg_d, xs, xd, hours, mode):
    """Reference price = midpoint of the local admissible interval (Deliverable 2 §2.4).
    'l2': bounds given by accepted orders only; 'complete': rejected orders also tighten
    the interval (rejected sell => upper bound, rejected buy => lower bound)."""
    ref, bounds = {}, {}
    for z in ZONES:
        for h in hours:
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


#---------------------------------------------------------------------------------------------------
# 5.3  P2: quadratic program of the prices
#   Mode 'complete': conditions (1), (2) and (14) of the paper, multiplier ν of Burkina Faso;
#   objective: sum of the squared deviations from the reference prices (eq. 15 of the paper),
#   hence unique prices. Mode 'l2': the restricted rule of Deliverable 2, kept for comparison,
#   with the total distance to the reference prices (absolute deviations, linearised).
#---------------------------------------------------------------------------------------------------
def _build_pricing(seg_s, seg_d, xs, xd, fl, hours, ntc, pairs, alpha_active, mode, quadratic=False):
    ref, _ = _reference_prices(seg_s, seg_d, xs, xd, hours, mode)
    mp = ConcreteModel()
    mp.pi = Var(ZONES, hours, bounds=(P_MIN, P_MAX))
    if quadratic and mode == 'complete':
        # Objective (15) of the paper: sum of the squared deviations. Strictly convex in P, so the
        # published price vector is unique (Section 2.7).
        mp.obj = Objective(expr=sum((mp.pi[z, h] - ref[z, h]) ** 2 for z in ZONES for h in hours),
                           sense=minimize)
    else:
        # Sum of the absolute deviations, linearised with e+ and e-: kept for mode 'l2' (prices not
        # always unique).
        mp.ep = Var(ZONES, hours, domain=NonNegativeReals)
        mp.en = Var(ZONES, hours, domain=NonNegativeReals)
        mp.obj = Objective(expr=sum(mp.ep[z, h] + mp.en[z, h] for z in ZONES for h in hours), sense=minimize)
        mp.refc = ConstraintList()
        for z in ZONES:
            for h in hours:
                mp.refc.add(mp.pi[z, h] - ref[z, h] == mp.ep[z, h] - mp.en[z, h])
    mp.sc = ConstraintList()
    if mode == 'l2':
        # Constraints (8)-(12) of Deliverable 2, as implemented in the notebook
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

    # Mode 'complete': full KKT conditions
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
    mp.mup = Var(pairs, hours, domain=NonNegativeReals)   # multiplier of f <= NTC
    mp.mum = Var(pairs, hours, domain=NonNegativeReals)   # multiplier of f >= -NTC
    mp.lam = Var(hours, domain=NonNegativeReals)          # multiplier of the α constraint
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


#===================================================================================================
# BLOCK 6 — CHECKS AND RULES APPLIED AROUND THE PRICES
#---------------------------------------------------------------------------------------------------
# Functions called by the algorithm (BLOCK 8) after P1bis or after P2: status of the blocks,
# check of the published prices, sharing of equal-price orders.
#===================================================================================================

#---------------------------------------------------------------------------------------------------
# 6.1  Paradoxical blocks (PAB / PRB, families and exclusive groups)
#   Surplus of each block at the published prices. PAB: an accepted parent is assessed with its
#   accepted children (family rule of EUPHEMIA), a child alone. PRB: a rejected block is assessed
#   with the blocks its acceptance depends on, that is, its family and its exclusive group.
#---------------------------------------------------------------------------------------------------
def _price_blocks(blocks, y, prices, parent_of=None, groups=None):
    """Status of each block at the given prices: OK, PAB, PRB, inactive.

    PAB (block accepted at a loss). Family rule of EUPHEMIA: an accepted parent is assessed with its
    accepted children, and a parent at a loss remains accepted if its children compensate its loss; a
    child is assessed alone, since its parent cannot support it. An accepted block is a PAB if
    F_k < -PRICE_TOL * Q_k (F_k: surplus of the family, Q_k: its energy).

    PRB (rejected block that would have gained at the published prices). A rejected block is paradoxical
    only if its owner would have preferred an outcome that the links between its blocks allowed:
      - family whose parent is rejected: the children are not assessed alone, since they could not be
        accepted without their parent. The family is assessed: the parent and those of its children that
        gain at the published prices. If its surplus exceeds PRICE_TOL per MWh, the parent and these
        children are PRB (prb_basis = 'family');
      - exclusive group with an accepted block k: a rejected block j of the group is PRB only if its
        owner would have preferred it to k, that is, if its surplus exceeds that of k by more than
        PRICE_TOL per MWh of j (prb_basis = 'group');
      - exclusive group without accepted block: only the best block of the group can be PRB, since only
        one could be accepted (prb_basis = 'group');
      - other rejected blocks, including the rejected child of an accepted parent: surplus > PRICE_TOL
        per MWh (prb_basis = 'block').
    A parent that belongs to an exclusive group is assessed there with its family, and a child that
    belongs to a group whose parent is rejected follows its family. A child whose group already has an
    accepted block is not counted in the family of its parent, since it could not be accepted at the
    same time."""
    parent_of = parent_of or {}
    groups = groups or []
    children = {}                                   # parent -> list of its children
    for c, p in parent_of.items():
        children.setdefault(p, []).append(c)
    group_of = {b: g for g in groups for b in g}    # block -> list of the blocks of its exclusive group

    def accepted(b):
        return bool(y.get(b, 0))

    # 1. Surplus and energy of each block, taken alone
    surplus, energy = {}, {}
    for b, blk in enumerate(blocks):
        hb = blk.active_hours
        if not hb:
            continue
        surplus[b] = sum((prices[blk.zone, h] - blk.p) * blk.q for h in hb) if blk.side == 'S' \
            else sum((blk.p - prices[blk.zone, h]) * blk.q for h in hb)
        energy[b] = blk.q * len(hb)

    def blocked_by_group(b):
        """Another block of the exclusive group of b is accepted: b could not be."""
        return any(accepted(k) for k in group_of.get(b, []) if k != b)

    def option(b):
        """What the owner would have obtained by having b (a rejected block) accepted: b and, if it is a
        parent, those of its children that gain at the published prices and that their group does not
        exclude. Returns (surplus, energy, blocks concerned)."""
        fam = [b] + [c for c in children.get(b, [])
                     if c in surplus and surplus[c] > 0 and not blocked_by_group(c)]
        return sum(surplus[k] for k in fam), sum(energy[k] for k in fam), fam

    def actual(k):
        """Surplus and energy obtained by the accepted block k and its accepted children."""
        fam = [k] + [c for c in children.get(k, []) if accepted(c) and c in surplus]
        return sum(surplus[i] for i in fam), sum(energy[i] for i in fam)

    def child_of_rejected_parent(b):
        p = parent_of.get(b)
        return p is not None and not accepted(p)

    # 2. PRB status of the rejected blocks: (status, basis) per block; OK by default
    prb = {}

    def set_family(b, is_prb, fam):
        """Status of a rejected parent assessed with its family, and of its children."""
        basis = 'family' if children.get(b) else 'block'
        prb[b] = ('PRB' if is_prb else 'OK', basis)
        for c in children.get(b, []):
            if c in surplus and not accepted(c):
                prb[c] = ('PRB' if (is_prb and c in fam) else 'OK', 'family')

    # 2a. Exclusive groups
    for g in groups:
        members = [b for b in g if b in surplus and not child_of_rejected_parent(b)]
        acc = [k for k in members if accepted(k)]
        rejected = [j for j in members if not accepted(j)]
        if acc:
            v_acc, _ = actual(acc[0])
            for j in rejected:
                v, e, fam = option(j)
                is_prb = v - v_acc > PRICE_TOL * e
                if children.get(j):
                    set_family(j, is_prb, fam)
                prb[j] = ('PRB' if is_prb else 'OK', 'group')
        elif rejected:
            best = max(rejected, key=lambda j: option(j)[0])
            for j in rejected:
                v, e, fam = option(j)
                is_prb = (j == best) and v > PRICE_TOL * e
                if children.get(j):
                    set_family(j, is_prb, fam)
                prb[j] = ('PRB' if is_prb else 'OK', 'group')

    # 2b. Rejected parents outside any group: assessed with their family
    for b in children:
        if b in surplus and not accepted(b) and b not in group_of:
            v, e, fam = option(b)
            set_family(b, v > PRICE_TOL * e, fam)

    # 2c. Other rejected blocks: assessed alone
    for b in surplus:
        if not accepted(b) and b not in prb:
            if child_of_rejected_parent(b):
                prb[b] = ('OK', 'family')      # parent without active hour: the child could not pass
            else:
                prb[b] = ('PRB' if surplus[b] > PRICE_TOL * energy[b] else 'OK', 'block')

    # 3. Status of each block
    out = []
    for b, blk in enumerate(blocks):
        hb = blk.active_hours
        if not hb:
            out.append(dict(name=blk.name, zone=blk.zone, player=blk.player, side=blk.side,
                            quantity=blk.q, price=blk.p, hours=blk.hours, accepted=False,
                            avg_price=None, surplus=0.0, status='inactive'))
            continue
        avg = sum(prices[blk.zone, h] for h in hb) / len(hb)
        acc = accepted(b)
        F, Q = actual(b) if acc else (0.0, 0.0)
        if acc:
            # Family of an accepted block: itself and its accepted children (a child has no children)
            status = 'PAB' if F < -PRICE_TOL * Q else 'OK'
            basis = 'family' if any(accepted(c) for c in children.get(b, [])) else 'block'
        else:
            status, basis = prb[b]
        out.append(dict(name=blk.name, zone=blk.zone, player=blk.player, side=blk.side,
                        quantity=blk.q, price=blk.p, hours=blk.hours, parent=blk.parent, group=blk.group,
                        accepted=acc, avg_price=round(avg, 2),
                        surplus=round(surplus[b] if acc else 0.0, 1),
                        surplus_if_accepted=round(surplus[b], 1),
                        family_surplus=round(F, 1), status=status, prb_basis=basis))
    return out


#---------------------------------------------------------------------------------------------------
# 6.2  Consistency diagnostics
#   Counts, per hour, the paradoxically rejected or accepted orders and the price gaps across
#   unsaturated lines (figures of Section 4.2 of the paper).
#---------------------------------------------------------------------------------------------------
# ── Consistency diagnostics ───────────────────────────────────────
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

#---------------------------------------------------------------------------------------------------
# 6.3  Sharing of equal-price orders (pro rata)
#   Applied after P1bis: shares the accepted quantity of a group of orders of the same zone,
#   side, hour and price (pro rata, submission order or solver).
#---------------------------------------------------------------------------------------------------
# ── Sharing rule for equal-price orders ───────────────────────────
def _apply_tie_rule(seg_s, seg_d, xs, xd, hours, rule):
    """Shares, among orders of the same zone, side, hour and price, the quantity the solver accepted for
    the group: 'prorata' (proportional to offered quantities), 'order' (submission order, first come
    first served), 'solver' (allocation left to the solver). The group's accepted total is unchanged:
    neither welfare, nor volume, nor the set of admissible prices moves.
    Returns the number of (zone, hour, side, price) groups whose allocation was modified."""
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
                    continue                       # group fully rejected or accepted: nothing to share
                if rule == 'prorata':
                    share = acc / total
                    new = {i: share for i in idx}
                else:                              # 'order': first submitted, first served
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


#===================================================================================================
# BLOCK 7 — MINIMUM INCOME CONDITION (MIC)
#---------------------------------------------------------------------------------------------------
# As in EUPHEMIA, a MIC applies to the sell segments of an actor, never to blocks.
#===================================================================================================

#---------------------------------------------------------------------------------------------------
# 7.1  Reading and validation of the MICs
#   Mic record; a MIC without sell segment or with a negative term is refused.
#---------------------------------------------------------------------------------------------------
# ── Minimum Income Condition ──────────────────────────────────────
@dataclass
class Mic:
    zone: str
    player: str
    actor: str
    fixed_term: float
    variable_term: float

def _build_mic(mic_rows, seg_s):
    """Reads the minimum income conditions. As in EUPHEMIA, a MIC applies to the sell segments (stepwise
    orders) of an actor, never to blocks: the actor must therefore have at least one sell segment in the
    zone, and both terms must be non-negative."""
    sellers = {(s.zone, s.player, s.actor) for s in seg_s}
    out = []
    for r in mic_rows:
        who = f"{r.get('actor', '?')} ({r.get('zone', '?')})"
        if r.get('zone') not in ZONES:
            raise ClearingError(f"Minimum income condition of {who}: unknown zone.")
        ft, vt = float(r.get('fixed_term') or 0.0), float(r.get('variable_term') or 0.0)
        if ft < 0 or vt < 0:
            raise ClearingError(f"Minimum income condition of {who}: the fixed and variable terms must be non-negative.")
        if (r['zone'], r.get('player', ''), r['actor']) not in sellers:
            raise ClearingError(f"Minimum income condition of {who}: the actor has no sell segment in this zone "
                                "(a minimum income condition applies to stepwise sell orders, not to blocks).")
        out.append(Mic(r['zone'], r.get('player', ''), r['actor'], ft, vt))
    return out


#---------------------------------------------------------------------------------------------------
# 7.2  Check of the MICs at final prices
#   Income and accepted energy of each actor, compared with fixed term + variable term ×
#   energy (tolerance ε_m); list of the actors to withdraw.
#---------------------------------------------------------------------------------------------------
def _mic_check(mics, seg_s, xs, prices, hours, withdrawn):
    """Income of each actor under a MIC at final prices, compared with fixed term + variable term × volume.
    An actor with nothing accepted trivially satisfies its condition (inactive order)."""
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
        # Blocks are not counted: a MIC applies to the sell segments only (as in EUPHEMIA)
        req = m.fixed_term + m.variable_term * acc
        sat = acc <= 1e-6 or inc >= req - MIC_TOL
        results.append(dict(base, accepted_mwh=round(acc, 1), income=round(inc, 1), required=round(req, 1), satisfied=sat, withdrawn=False))
        if not sat:
            to_withdraw.append(key)
    return results, to_withdraw


#===================================================================================================
# BLOCK 8 — COMPLETE ALGORITHM: P1 → P1bis → P2 AND THE PARADOXICAL-BLOCK LOOP
#---------------------------------------------------------------------------------------------------
# The procedure of Section 2.7 of the paper: P1, P1bis (with a fallback on P1), pro rata sharing,
# P2 (with a fallback), check of the blocks; a PAB is rejected, or the configuration of its family
# is excluded by a cut, and the sequence is run again until none remains.
#===================================================================================================

# ── P1 → P1bis → P2 sequence with the PAB loop ────────────────────
def _solve_sequence(seg_s, seg_d, blocks, parent_of, groups, hours, ntc, pairs, alpha_active,
                    solver, pricing, pab_rule, max_pab_iter, tie_rule, notes):
    fixed_y, iterations, unforceable = {}, 0, set()
    cuts = []                                       # family cuts already added to P1
    children = {}                                   # parent -> list of its children
    for c, p in parent_of.items():
        children.setdefault(p, []).append(c)
    # A family with n children has at most 2^n configurations with its parent accepted: the number
    # of cuts is finite, and it is added to the iteration limit.
    max_iter = max_pab_iter + sum(2 ** len(ch) for ch in children.values())
    # Solver of P2. Rule 'complete' requires a quadratic solver: without it, the clearing stops with an
    # installation message rather than publishing prices computed with another rule.
    # Rule 'l2' (comparison) keeps the linear objective and the solver of P1.
    qp_solver, qp_name = _get_qp_solver() if pricing == 'complete' else (None, None)
    if pricing == 'complete' and qp_solver is None:
        raise ClearingError(
            "P2 needs a quadratic programming solver: Gurobi, or HiGHS through Pyomo >= 6.9.3. "
            "Install or upgrade them with:  pip install --upgrade \"pyomo>=6.9.3\" highspy")
    quad = qp_solver is not None
    p2_solver = qp_solver if quad else solver
    while True:
        iterations += 1
        m1 = _build_primal(seg_s, seg_d, blocks, parent_of, groups, hours, ntc, pairs,
                           objective='welfare', fixed_y=fixed_y, cuts=cuts)
        ok, status = _try_solve(solver, m1)
        if not ok:
            forced = [b for b, v in fixed_y.items() if v == 1]
            if not forced:
                raise ClearingError(f"P1 (welfare): no optimal solution ({status}).")
            # Forcing one or more PRBs to acceptance (rule 'l2') is physically impossible: release them.
            for b in forced:
                del fixed_y[b]; unforceable.add(b)
            notes.append("Unforceable PRBs (P1 infeasible), released: " + ", ".join(blocks[b].name for b in forced))
            continue
        W_star = float(value(m1.welfare))
        xs, xd, fl, y = _extract(m1, seg_s, seg_d, blocks, hours, pairs)
        # With blocks, P1 is a MILP stopped at the relative gap MIP_GAP: the welfare of the returned
        # solution is not necessarily the optimum of the linear program with the blocks fixed at u*.
        # If P1bis took that value as W*, it could keep a dispatch that is not optimal for this linear
        # program, and that no price supports any more. This linear program is therefore solved: its
        # optimum is the W* of P1bis, and its solution replaces that of the MILP (fallback of P1bis and P2).
        if blocks:
            m1_lp = _build_primal(seg_s, seg_d, blocks, parent_of, groups, hours, ntc, pairs,
                                  objective='welfare', fixed_y=dict(y))
            ok_lp, status_lp = _try_solve(solver, m1_lp)
            if ok_lp:
                m1 = m1_lp
                W_star = float(value(m1.welfare))
                xs, xd, fl, _ = _extract(m1, seg_s, seg_d, blocks, hours, pairs)
            else:
                notes.append(f"P1 with the blocks fixed: no optimal solution ({status_lp}); "
                             "the welfare of the MILP solution is used as W*.")
        tie_break = 'none'

        # P1bis: maximum volume among welfare-optimal solutions (ε = 0)
        if seg_s or seg_d:
            m2 = _build_primal(seg_s, seg_d, blocks, parent_of, groups, hours, ntc, pairs,
                               objective='volume', welfare_floor=W_star, fixed_y=dict(y))
            ok, status = _try_solve(solver, m2)
            if ok:
                xs, xd, fl, _ = _extract(m2, seg_s, seg_d, blocks, hours, pairs)
                tie_break = 'exact'
            else:
                notes.append(f"P1bis: volume tie-break impossible ({status}); P1 solution kept.")
        tie_groups = _apply_tie_rule(seg_s, seg_d, xs, xd, hours, tie_rule)

        # P2
        mp = _build_pricing(seg_s, seg_d, xs, xd, fl, hours, ntc, pairs, alpha_active, pricing, quadratic=quad)
        ok, status = _try_solve(p2_solver, mp)
        pricing_feasible = ok
        if not ok and tie_break == 'exact':
            xs, xd, fl, y = _extract(m1, seg_s, seg_d, blocks, hours, pairs)
            tie_break = 'fallback_p1'
            tie_groups = _apply_tie_rule(seg_s, seg_d, xs, xd, hours, tie_rule)
            mp = _build_pricing(seg_s, seg_d, xs, xd, fl, hours, ntc, pairs, alpha_active, pricing, quadratic=quad)
            ok, status = _try_solve(p2_solver, mp)
            pricing_feasible = ok
            notes.append("P2: the P1bis solution admitted no admissible price; prices computed on the P1 solution.")
        if not ok:
            raise ClearingError(f"P2 (prices): no solution ({status}). Check the orders (prices out of bounds, inconsistencies).")
        prices = {(z, h): float(value(mp.pi[z, h])) for z in ZONES for h in hours}

        # Paradoxical blocks
        block_results = _price_blocks(blocks, y, prices, parent_of, groups) if blocks else []
        to_fix, new_cuts = {}, []
        for b, br in enumerate(block_results):
            if br['status'] == 'PAB' and pab_rule == 'euphemia' and (b in children or b in parent_of):
                # Block of a family: as with the cuts of EUPHEMIA, only the current configuration of the
                # family (parent + children) is forbidden; P1 will choose the best among the others.
                p = parent_of.get(b, b)
                config = tuple((k, y[k]) for k in [p] + children[p])
                if config not in cuts and config not in new_cuts:
                    new_cuts.append(config)
            elif br['status'] == 'PAB' and pab_rule in ('euphemia', 'l2') and fixed_y.get(b) != 0:
                # Block without family: rejecting it forbids its only accepted configuration.
                to_fix[b] = 0
            elif br['status'] == 'PRB' and pab_rule == 'l2' and b not in fixed_y and b not in unforceable:
                # In a PRB family, only the parent is forced: its children are left to P1.
                if not (b in parent_of and br.get('prb_basis') == 'family'):
                    to_fix[b] = 1
        # Rule 'l2' only: when a parent and one of its children are both PAB, the child is rejected
        # first. With 'euphemia', the blocks of a family go through the cuts.
        for c, p in parent_of.items():
            if to_fix.get(c) == 0 and to_fix.get(p) == 0:
                del to_fix[p]
        if (not to_fix and not new_cuts) or iterations > max_iter:
            if to_fix or new_cuts:
                notes.append("PAB/PRB loop stopped at the maximum number of iterations.")
            break
        fixed_y.update(to_fix)
        cuts.extend(new_cuts)
        if to_fix:
            notes.append("Iteration %d: blocks fixed %s" % (iterations, {blocks[b].name: v for b, v in to_fix.items()}))
        for config in new_cuts:
            notes.append("Iteration %d: family configuration excluded %s"
                         % (iterations, {blocks[k].name: v for k, v in config}))
    return dict(xs=xs, xd=xd, fl=fl, y=y, prices=prices, block_results=block_results, W_star=W_star,
                iterations=iterations, fixed_y=fixed_y, tie_break=tie_break,
                pricing_feasible=pricing_feasible, tie_groups=tie_groups,
                pricing_objective=('quadratic' if quad else 'absolute'))

#===================================================================================================
# BLOCK 9 — ENTRY POINT run_clearing
#---------------------------------------------------------------------------------------------------
# The function called by every user of the engine (scripts, CLI, tests, website). It prepares the
# orders, runs the MIC loop around the algorithm of BLOCK 8, then computes and formats every result.
# All the results of the working paper are produced by this function.
#===================================================================================================
# ── Main engine ───────────────────────────────────────────────────
def run_clearing(supply_rows=None, demand_rows=None, horizon=24, ntc_override=None, *,
                 block_rows=None, mic_rows=None, hours=None, fill_missing_zones=False, fill_mode=None,
                 pricing='complete', pab_rule='euphemia', tie_rule='prorata',
                 max_pab_iter=None, max_mic_iter=None, reference_rows=None):
    """
    Full clearing P1 → P1bis → P2.

    supply_rows / demand_rows : rows in the database format (None to use the reference data).
    block_rows   : block, linked and exclusive orders (block_orders table format); None = none.
    mic_rows     : minimum income conditions (zone, player, actor, fixed_term, variable_term); None = none.
    horizon      : 24 (full day) or 1; ignored when `hours` is given.
    hours        : list of simulated hours (e.g. [19]); defaults to range(horizon).
    ntc_override : {(u, v): MW}; otherwise the database NTC (if defined), otherwise the defaults.
    fill_missing_zones : (compatibility) True is equivalent to fill_mode='zones'.
    fill_mode    : 'none' (participants' orders only), 'zones' (zones without any submission filled from the
                   reference), 'actors' (background actors: every reference actor is kept, except those of a
                   participant's zone whose name matches the participant's organisation or one of its orders,
                   which are replaced by the participant's orders).
    pricing      : 'complete' (full KKT, v2) or 'l2' (constraints (8)-(12) of Deliverable 2).
    pab_rule     : 'euphemia' (iterative rejection of PABs, PRBs tolerated), 'l2' (PABs fixed to 0 and
                   PRBs fixed to 1, Deliverable 2 §3.3) or 'none' (detection only).
    tie_rule     : sharing of equal-price orders: 'prorata' (default), 'order', 'solver'.
    reference_rows : (supply_rows, demand_rows) to use as reference data instead of the Deliverable 2 set
                   (teaching scenarios), for the demonstration and for filling zones.
    Returns a dict: prices, flows, dispatch, welfare, volume, summary.
    """
    #-----------------------------------------------------------------------------------------------
    # 9.1  Rule checks
    #   Start of the timer and check of the names of the pricing, block and sharing rules.
    #-----------------------------------------------------------------------------------------------
    t_total = time.time()
    if pricing not in PRICING_MODES:
        raise ClearingError(f"Unknown pricing mode: {pricing}")
    if pab_rule not in PAB_RULES:
        raise ClearingError(f"Unknown PAB rule: {pab_rule}")
    if tie_rule not in TIE_RULES:
        raise ClearingError(f"Unknown sharing rule: {tie_rule}")
    notes = []

    #-----------------------------------------------------------------------------------------------
    # 9.2  Simulated hours
    #   The 24 hours by default; a list of hours can be given (one-hour examples).
    #-----------------------------------------------------------------------------------------------
    # ── Simulated hours ───────────────────────────────────────────
    if hours is None:
        hours = list(range(int(horizon)))
    hours = [int(h) for h in hours]
    if not hours or any(h < 0 or h > 23 for h in hours):
        raise ClearingError("Simulated hours must be between 0 and 23.")

    #-----------------------------------------------------------------------------------------------
    # 9.3  Data: choice of the orders
    #   Orders given or reference data; fill modes 'zones' and 'actors' used by the training
    #   website.
    #-----------------------------------------------------------------------------------------------
    # ── Data ──────────────────────────────────────────────────────
    reference_zones = []
    def _ref(zones=None):
        if reference_rows is None:
            return default_rows(zones)
        rs, rd = reference_rows
        if zones is None:
            return list(rs), list(rd)
        return [r for r in rs if r['zone'] in zones], [r for r in rd if r['zone'] in zones]
    if supply_rows is None and demand_rows is None:
        supply_rows, demand_rows = _ref()
        reference_zones = list(ZONES)
        notes.append("Reference data used for all 14 zones.")
    else:
        supply_rows = list(supply_rows or [])
        demand_rows = list(demand_rows or [])
        if fill_mode is None:
            fill_mode = 'zones' if fill_missing_zones else 'none'
        if fill_mode not in ('none', 'zones', 'actors'):
            raise ClearingError(f"Unknown fill mode: {fill_mode}")
        if fill_mode == 'zones':
            covered = {r['zone'] for r in supply_rows} | {r['zone'] for r in demand_rows} \
                    | {r['zone'] for r in (block_rows or [])}
            missing = [z for z in ZONES if z not in covered]
            if missing:
                ds, dd = _ref(zones=missing)
                supply_rows += ds
                demand_rows += dd
                reference_zones = missing
                notes.append(f"Zones filled with reference data: {', '.join(missing)}.")
        elif fill_mode == 'actors':
            keys = {}
            for r in supply_rows + demand_rows + list(block_rows or []):
                for nm in (r.get('player'), r.get('actor'), r.get('name')):
                    if nm:
                        keys.setdefault(r['zone'], set()).add(_name_key(nm))
            def replaced(row):
                k = _name_key(row['actor'])
                return any(k == other or k.split(' ')[0] == other.split(' ')[0] or other in k or k in other
                           for other in keys.get(row['zone'], ()) if other)
            ds, dd = _ref()
            kept_s = [r for r in ds if not replaced(r)]; kept_d = [r for r in dd if not replaced(r)]
            gone = sorted({r['actor'] for r in ds + dd if replaced(r)})
            supply_rows += kept_s
            demand_rows += kept_d
            reference_zones = sorted({r['zone'] for r in kept_s + kept_d}, key=ZONES.index)
            notes.append(f"Background actors: {len(kept_s) + len(kept_d)} reference segments kept"
                         + (f"; actors replaced by participants: {', '.join(gone)}." if gone else "."))
    #-----------------------------------------------------------------------------------------------
    # 9.4  Validation and construction
    #   Calls to the functions of BLOCK 3 and BLOCK 7, and default iteration limits.
    #-----------------------------------------------------------------------------------------------
    block_rows = list(block_rows or [])
    validate_inputs(supply_rows, demand_rows, block_rows)

    seg_s_all, seg_d = _build_segments(supply_rows, demand_rows, hours)
    blocks_all = _build_blocks(block_rows, hours)
    mics = _build_mic(mic_rows or [], seg_s_all)
    if max_mic_iter is None:
        max_mic_iter = len(mics) + 1
    if max_pab_iter is None:
        max_pab_iter = 2 * len(blocks_all) + 1

    #-----------------------------------------------------------------------------------------------
    # 9.5  Line capacities (NTC)
    #   Values passed by the caller, else those modified in the database of the website, else the
    #   defaults; choice of the solver.
    #-----------------------------------------------------------------------------------------------
    # ── NTC: override > database > defaults ───────────────────────
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
                    notes.append("NTC modified by the administrator on: " + ", ".join(changed) + ".")
        except Exception as e:          # no database: default values
            logger.debug("Default NTC (%s)", e)
    pairs = list(ntc.keys())
    alpha_active = all(l in ntc for l in ALPHA_LINES)

    solver, solver_name = _get_solver()
    logger.info("Solver %s | %d sell segments, %d buy segments, %d blocks, %d MIC, %d hours",
                solver_name, len(seg_s_all), len(seg_d), len(blocks_all), len(mics), len(hours))

    #-----------------------------------------------------------------------------------------------
    # 9.6  MIC loop
    #   At each round, the complete algorithm (BLOCK 8) then the check of the MICs; the actors
    #   whose MIC fails are withdrawn and the round is run again.
    #-----------------------------------------------------------------------------------------------
    # ── MIC loop around the P1 → P1bis → P2 sequence ──────────────
    withdrawn = set()
    coverage = {}        # coverage ratio (income / required income) of each actor when it was withdrawn
    at_withdrawal = {}   # energy, income and required income of each actor when it was withdrawn
    mic_iter = 0
    while True:
        mic_iter += 1
        seg_s = [s for s in seg_s_all if (s.zone, s.player, s.actor) not in withdrawn]
        blocks = blocks_all          # a MIC withdraws sell segments only, never blocks
        parent_of, groups = _resolve_links(blocks, notes if mic_iter == 1 else [])
        sol = _solve_sequence(seg_s, seg_d, blocks, parent_of, groups, hours, ntc, pairs, alpha_active,
                              solver, pricing, pab_rule, max_pab_iter, tie_rule, notes)
        mic_results, to_withdraw = _mic_check(mics, seg_s, sol['xs'], sol['prices'], hours, withdrawn)
        if not to_withdraw or mic_iter > max_mic_iter:
            if to_withdraw:
                notes.append("MIC loop stopped at the maximum number of iterations.")
            break
        for r in mic_results:
            k = (r['zone'], r['player'], r['actor'])
            if k in to_withdraw:
                coverage[k] = r['income'] / r['required'] if r['required'] > 0 else float('inf')
                at_withdrawal[k] = dict(accepted_mwh=r['accepted_mwh'], income=r['income'],
                                        required=r['required'], coverage=round(coverage[k], 3))
        withdrawn |= set(to_withdraw)
        notes.append("MIC not satisfied, orders withdrawn: " + ", ".join(f"{a} ({z})" for z, _, a in to_withdraw) + ".")


    #-----------------------------------------------------------------------------------------------
    # 9.7  MIC reinsertion
    #   As the "PRMIC reinsertion" of EUPHEMIA (section 7.7): each withdrawn actor is tried again,
    #   from the highest coverage ratio to the lowest.
    #-----------------------------------------------------------------------------------------------
    # Several actors may have been withdrawn together; once the others have left, the price may have risen
    # and one of them would now cover its costs. Each withdrawn actor is tried again, starting with the
    # highest coverage ratio (the closest to meeting its condition; a public rule that depends only on the
    # orders and the prices). A reinsertion is kept if every MIC remains satisfied and the welfare does not
    # decrease; after a successful reinsertion, the list of candidates is restarted.
    reinserted = []
    if withdrawn and not to_withdraw:
        improved = True
        while improved and withdrawn:
            improved = False
            for key in sorted(withdrawn, key=lambda k: (-coverage.get(k, 0.0), k)):
                trial = withdrawn - {key}
                seg_t = [s for s in seg_s_all if (s.zone, s.player, s.actor) not in trial]
                try:
                    sol_t = _solve_sequence(seg_t, seg_d, blocks, parent_of, groups, hours, ntc, pairs, alpha_active,
                                            solver, pricing, pab_rule, max_pab_iter, tie_rule, [])
                except ClearingError:
                    continue
                res_t, fail_t = _mic_check(mics, seg_t, sol_t['xs'], sol_t['prices'], hours, trial)
                if not fail_t and sol_t['W_star'] >= sol['W_star'] - 1e-6 * max(1.0, abs(sol['W_star'])):
                    withdrawn, seg_s, sol, mic_results = trial, seg_t, sol_t, res_t
                    reinserted.append(key)
                    improved = True
                    break
    if reinserted:
        notes.append("MIC reinsertion: orders reinstated for " + ", ".join(f"{a} ({z})" for z, _, a in reinserted) + ".")

    # After a withdrawal, energy and income are zero and do not say why the actor was withdrawn: its values
    # at the time of the withdrawal are published too, with the coverage ratio of every actor.
    for r in mic_results:
        k = (r['zone'], r['player'], r['actor'])
        if r['withdrawn']:
            r['at_withdrawal'] = at_withdrawal.get(k)
        else:
            r['coverage'] = round(r['income'] / r['required'], 3) if r['required'] > 0 else None

    #-----------------------------------------------------------------------------------------------
    # 9.8  Final solution and volume
    #   Solution of the last round and traded volume (energy sold, blocks included).
    #-----------------------------------------------------------------------------------------------
    xs, xd, fl, y, prices = sol['xs'], sol['xd'], sol['fl'], sol['y'], sol['prices']
    block_results = sol['block_results']
    S, D, B = range(len(seg_s)), range(len(seg_d)), range(len(blocks))
    vol = sum(seg_s[s].qty[h] * xs[s, h] for s in S for h in hours if seg_s[s].qty[h] > 0) \
        + sum(blocks[b].q * len(blocks[b].active_hours) * y.get(b, 0) for b in B if blocks[b].side == 'S')


    #-----------------------------------------------------------------------------------------------
    # 9.9  Prices, flows and generation
    #   Published prices (to the cent), flows per line and energy generated per profile type,
    #   hour by hour.
    #-----------------------------------------------------------------------------------------------
    # ── Results ───────────────────────────────────────────────────
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

    #-----------------------------------------------------------------------------------------------
    # 9.10  Results per actor
    #   Energy offered and accepted, income or spending, surplus, average price and rejected
    #   orders of each actor.
    #-----------------------------------------------------------------------------------------------
    # Results per actor (trader view)
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
    for s in seg_s_all:                       # actors withdrawn by the MIC
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

    #-----------------------------------------------------------------------------------------------
    # 9.11  Results per zone and per line, welfare
    #   Generation, consumption, surplus and weighted average price per zone; congestion rent
    #   and average flow per line; hourly and total welfare.
    #-----------------------------------------------------------------------------------------------
    # Breakdown per zone and congestion rent
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
        # Average price weighted by the consumption of the zone (the average price paid by a consumer);
        # simple average of the hours when the zone has no accepted consumption.
        load_h = {h: sum(seg_d[d].qty[h] * xd[d, h] for d in D if seg_d[d].zone == z and seg_d[d].qty[h] > 0)
                     + sum(blocks[b].q * y.get(b, 0) for b in B
                           if blocks[b].zone == z and blocks[b].side == 'D' and h in blocks[b].active_hours)
                  for h in hours}
        tot_load = sum(load_h.values())
        avg_simple = sum(prices[z, h] for h in hours) / n
        avg_weighted = (sum(prices[z, h] * load_h[h] for h in hours) / tot_load) if tot_load > 1e-9 else avg_simple
        zones_out[z] = dict(generation_mwh=round(gen, 1), load_mwh=round(load, 1), net_position=round(gen - load, 1),
                            producer_surplus=round(ps, 1), consumer_surplus=round(cs, 1),
                            avg_price=round(avg_weighted, 2), avg_price_simple=round(avg_simple, 2),
                            no_trade_hours=[h for h in hours if
                                            all(seg_s[s].zone != z or seg_s[s].qty[h] <= 0 or xs[s, h] < X_TOL for s in S) and
                                            all(seg_d[d].zone != z or seg_d[d].qty[h] <= 0 or xd[d, h] < X_TOL for d in D) and
                                            not any(blocks[b].zone == z and h in blocks[b].active_hours and y.get(b, 0) for b in B)])
    lines_out = {}
    for u, v in pairs:
        rent = sum(fl[u, v, h] * (prices[v, h] - prices[u, h]) for h in hours)
        sat = sum(1 for h in hours if abs(fl[u, v, h]) >= ntc[(u, v)] - F_TOL)
        # avg_flow: average of the absolute values (use of the line, whichever the direction);
        # avg_net_flow: signed average (dominant direction: > 0 from u to v)
        lines_out[f"{u}->{v}"] = dict(ntc=ntc[(u, v)], congestion_rent=round(rent, 1), saturated_hours=sat,
                                      avg_flow=round(sum(abs(fl[u, v, h]) for h in hours) / n, 1),
                                      avg_net_flow=round(sum(fl[u, v, h] for h in hours) / n, 1))
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

    #-----------------------------------------------------------------------------------------------
    # 9.12  Diagnostics
    #   Consistency diagnostics (BLOCK 6.2), rules used, iterations, fixed blocks, withdrawn
    #   MICs, check of the identity welfare = CS + PS + rent, notes.
    #-----------------------------------------------------------------------------------------------
    diag = _diagnostics(seg_s, seg_d, xs, xd, fl, prices, hours, ntc, pairs, alpha_active)
    diag.update(dict(pricing_mode=pricing, pricing_objective=sol['pricing_objective'],
                     pricing_feasible=sol['pricing_feasible'], tie_break=sol['tie_break'],
                     tie_rule=tie_rule, tie_groups_adjusted=sol['tie_groups'],
                     pab_iterations=sol['iterations'], blocks_fixed={blocks[b].name: v for b, v in sol['fixed_y'].items()},
                     prb=[br['name'] for br in block_results if br['status'] == 'PRB'],
                     pab=[br['name'] for br in block_results if br['status'] == 'PAB'],
                     mic_iterations=mic_iter, mic_withdrawn=[f"{a} ({z})" for z, _, a in sorted(withdrawn)],
                     welfare_identity_gap=round(W_final - (cs_tot + ps_tot + cr_tot), 1),
                     notes=notes))


    #-----------------------------------------------------------------------------------------------
    # 9.13  Summary and output
    #   The summary and the returned dictionary: prices, flows, generation, welfare, volume,
    #   summary.
    #-----------------------------------------------------------------------------------------------
    # Detail of each segment, hour by hour, for the independent check of the prices (engine/checks.py)

    segments_out = [dict(zone=g.zone, player=g.player, actor=g.actor, segment=g.k, side=side, price=g.p,
                         offered={str(h): g.qty[h] for h in hours if g.qty[h] > 0},
                         accepted={str(h): round(g.qty[h] * x[i, h], 4) for h in hours if g.qty[h] > 0})
                    for segs, x, side in ((seg_s, xs, 'S'), (seg_d, xd, 'D')) for i, g in enumerate(segs)]

    summary = {
        'welfare':         round(W_final, 0),
        'volume':          round(vol, 0),
        'elapsed':         round(time.time() - t_total, 2),
        'solver':          solver_name,
        'mip_gap':         MIP_GAP,
        'horizon':         len(hours),
        'hours':           hours,
        'n_supply':        len(seg_s_all),
        'n_demand':        len(seg_d),
        'n_blocks':        len(blocks_all),
        'n_mic':           len(mics),
        'n_withdrawn':     len(withdrawn),
        'reference_zones': reference_zones,
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
        'segments':        segments_out,
    }
    logger.info("Clearing finished in %.2fs | W=%.0f | Vol=%.0f MWh | %s",
                summary['elapsed'], W_final, vol, diag)
    return {
        'prices':   prices_out,
        'flows':    flows_out,
        'dispatch': dispatch,
        'welfare':  W_final,
        'volume':   vol,
        'summary':  summary,
    }
