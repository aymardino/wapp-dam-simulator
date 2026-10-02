"""
WAPP Market Simulator — état partagé via SQLite
Toutes les sessions Streamlit (traders, admin) lisent et écrivent la même base.

v2 : table ntc (capacités modifiables), table block_orders (ordres bloc / liés / exclusifs),
clé (zone, trader) pour les participants, mode WAL, chemin configurable (WAPP_DB_PATH).
"""
import sqlite3, json, os
from datetime import datetime

DB_PATH = os.environ.get('WAPP_DB_PATH') or os.path.join(os.path.dirname(__file__), '..', 'data', 'market.db')

SESSION_DEFAULTS = {
    'phase': 'submission',      # submission | cleared
    'market_date': datetime.now().strftime('%Y-%m-%d'),
    'horizon': '24',            # 1 ou 24
    'hour': '19',               # heure simulée en mode 1 h
    'mode': 'multizone',
    'currency': 'USD',          # libellé monétaire affiché
    'lang': 'fr',               # fr | en
    'pricing': 'complete',      # complete | l2
    'pab_rule': 'euphemia',     # euphemia | l2 | none
    'tie_rule': 'prorata',      # prorata | order | solver
    'fill_missing': '1',        # 1 : zones sans soumission complétées par les données de référence
}


def get_conn():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# Colonnes attendues par cette version pour chaque table gérée ici
EXPECTED_COLUMNS = {
    'session':       ['key', 'value'],
    'supply_offers': ['zone', 'player', 'actor', 'segment', 'quantity', 'price', 'profile'],
    'demand_bids':   ['zone', 'player', 'actor', 'segment', 'quantity', 'price'],
    'block_orders':  ['zone', 'player', 'name', 'side', 'quantity', 'price', 'h_start', 'h_end', 'parent_name', 'excl_group'],
    'ntc':           ['u', 'v', 'mw'],
    'mic_conditions': ['zone', 'player', 'actor', 'fixed_term', 'variable_term'],
    'results':       ['run_at', 'welfare', 'volume', 'prices_json', 'flows_json', 'dispatch_json', 'summary_json'],
}


def _columns(c, table):
    return [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]


def _migrate_legacy_tables(c):
    """Une table portant le même nom qu'une table de cette version mais avec d'autres colonnes
    (créée par une version antérieure du code) est convertie si on sait le faire, sinon renommée
    en <table>_legacy_<horodatage> pour ne jamais perdre de données."""
    stamp = datetime.now().strftime('%Y%m%d%H%M%S')
    for table, cols in EXPECTED_COLUMNS.items():
        existing = _columns(c, table)
        if not existing or set(cols) <= set(existing):
            continue
        if table == 'ntc' and {'zone_from', 'zone_to', 'value_mw'} <= set(existing):
            c.executescript("""
                CREATE TABLE ntc_v2 (u TEXT NOT NULL, v TEXT NOT NULL, mw REAL NOT NULL, PRIMARY KEY (u, v));
                INSERT OR IGNORE INTO ntc_v2 SELECT zone_from, zone_to, value_mw FROM ntc;
                DROP TABLE ntc;
                ALTER TABLE ntc_v2 RENAME TO ntc;
            """)
        else:
            c.execute(f"ALTER TABLE {table} RENAME TO {table}_legacy_{stamp}")


def init_db():
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("PRAGMA journal_mode=WAL")
    except sqlite3.DatabaseError:
        pass
    _migrate_legacy_tables(c)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS session (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS supply_offers (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            zone      TEXT NOT NULL,
            player    TEXT NOT NULL,
            actor     TEXT NOT NULL,
            segment   INTEGER NOT NULL,
            quantity  REAL NOT NULL,
            price     REAL NOT NULL,
            profile   TEXT NOT NULL DEFAULT 'baseload',
            submitted_at TEXT
        );
        CREATE TABLE IF NOT EXISTS demand_bids (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            zone      TEXT NOT NULL,
            player    TEXT NOT NULL,
            actor     TEXT NOT NULL,
            segment   INTEGER NOT NULL,
            quantity  REAL NOT NULL,
            price     REAL NOT NULL,
            submitted_at TEXT
        );
        CREATE TABLE IF NOT EXISTS block_orders (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            zone      TEXT NOT NULL,
            player    TEXT NOT NULL,
            name      TEXT NOT NULL,
            side      TEXT NOT NULL,
            quantity  REAL NOT NULL,
            price     REAL NOT NULL,
            h_start   INTEGER NOT NULL,
            h_end     INTEGER NOT NULL,
            parent_name TEXT,
            excl_group  TEXT,
            submitted_at TEXT
        );
        CREATE TABLE IF NOT EXISTS mic_conditions (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            zone      TEXT NOT NULL,
            player    TEXT NOT NULL,
            actor     TEXT NOT NULL,
            fixed_term    REAL NOT NULL DEFAULT 0,
            variable_term REAL NOT NULL DEFAULT 0,
            submitted_at TEXT
        );
        CREATE TABLE IF NOT EXISTS ntc (
            u   TEXT NOT NULL,
            v   TEXT NOT NULL,
            mw  REAL NOT NULL,
            PRIMARY KEY (u, v)
        );
        CREATE TABLE IF NOT EXISTS results (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at    TEXT,
            welfare   REAL,
            volume    REAL,
            prices_json    TEXT,
            flows_json     TEXT,
            dispatch_json  TEXT,
            summary_json   TEXT
        );
        CREATE TABLE IF NOT EXISTS players (
            zone      TEXT NOT NULL,
            player    TEXT NOT NULL,
            color     TEXT,
            connected_at TEXT,
            PRIMARY KEY (zone, player)
        );
    """)
    # Migration : ancienne table players (clé = zone seule) → clé (zone, player)
    row = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='players'").fetchone()
    if row and 'PRIMARY KEY (zone, player)' not in row['sql']:
        c.executescript("""
            CREATE TABLE players_v2 (
                zone TEXT NOT NULL, player TEXT NOT NULL, color TEXT, connected_at TEXT,
                PRIMARY KEY (zone, player));
            INSERT OR IGNORE INTO players_v2 SELECT zone, player, color, connected_at FROM players;
            DROP TABLE players;
            ALTER TABLE players_v2 RENAME TO players;
        """)
    for k, v in SESSION_DEFAULTS.items():
        c.execute("INSERT OR IGNORE INTO session VALUES (?,?)", (k, v))
    conn.commit()
    conn.close()


# ── Session ───────────────────────────────────────────────────────
def get_session():
    conn = get_conn()
    rows = conn.execute("SELECT key,value FROM session").fetchall()
    conn.close()
    s = dict(SESSION_DEFAULTS)
    s.update({r['key']: r['value'] for r in rows})
    return s


def set_session(key, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO session VALUES (?,?)", (key, str(value)))
    conn.commit()
    conn.close()


def reset_market():
    conn = get_conn()
    conn.execute("DELETE FROM supply_offers")
    conn.execute("DELETE FROM demand_bids")
    conn.execute("DELETE FROM block_orders")
    conn.execute("DELETE FROM mic_conditions")
    conn.execute("DELETE FROM results")
    conn.execute("UPDATE session SET value='submission' WHERE key='phase'")
    conn.commit()
    conn.close()


# ── Participants ──────────────────────────────────────────────────
ZONE_COLORS = {
    'NGA':'#e74c3c','BEN':'#e67e22','TGO':'#f1c40f','GHA':'#2ecc71',
    'CIV':'#1abc9c','BFA':'#3498db','MLI':'#9b59b6','SEN':'#ad1457',
    'GIN':'#e91e63','SLE':'#00bcd4','LBR':'#8bc34a','GNB':'#ff5722',
    'GMB':'#607d8b','NER':'#795548'
}


def register_player(zone, player_name):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO players VALUES (?,?,?,?)",
                 (zone, player_name, ZONE_COLORS.get(zone, '#888888'), datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_players():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM players ORDER BY zone, player").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Offres stepwise ───────────────────────────────────────────────
def save_supply_offers(zone, player, offers):
    """offers : liste de dicts {actor, segment, quantity, price, profile}"""
    conn = get_conn()
    conn.execute("DELETE FROM supply_offers WHERE zone=? AND player=?", (zone, player))
    now = datetime.now().isoformat()
    for o in offers:
        conn.execute(
            "INSERT INTO supply_offers (zone,player,actor,segment,quantity,price,profile,submitted_at) VALUES (?,?,?,?,?,?,?,?)",
            (zone, player, o['actor'], o['segment'], o['quantity'], o['price'], o.get('profile', 'baseload'), now))
    conn.commit()
    conn.close()


def save_demand_bids(zone, player, bids):
    """bids : liste de dicts {actor, segment, quantity, price}"""
    conn = get_conn()
    conn.execute("DELETE FROM demand_bids WHERE zone=? AND player=?", (zone, player))
    now = datetime.now().isoformat()
    for b in bids:
        conn.execute(
            "INSERT INTO demand_bids (zone,player,actor,segment,quantity,price,submitted_at) VALUES (?,?,?,?,?,?,?)",
            (zone, player, b['actor'], b['segment'], b['quantity'], b['price'], now))
    conn.commit()
    conn.close()


def _rows(sql, params=()):
    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_supply():
    return _rows("SELECT * FROM supply_offers ORDER BY zone,price")


def get_all_demand():
    return _rows("SELECT * FROM demand_bids ORDER BY zone,price DESC")


def get_zone_supply(zone):
    return _rows("SELECT * FROM supply_offers WHERE zone=? ORDER BY price", (zone,))


def get_zone_demand(zone):
    return _rows("SELECT * FROM demand_bids WHERE zone=? ORDER BY price DESC", (zone,))


# ── Ordres bloc, liés, exclusifs ──────────────────────────────────
def save_block_orders(zone, player, blocks):
    """blocks : liste de dicts {name, side ('S'|'D'), quantity, price, h_start, h_end, parent_name, excl_group}"""
    conn = get_conn()
    conn.execute("DELETE FROM block_orders WHERE zone=? AND player=?", (zone, player))
    now = datetime.now().isoformat()
    for b in blocks:
        conn.execute(
            "INSERT INTO block_orders (zone,player,name,side,quantity,price,h_start,h_end,parent_name,excl_group,submitted_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (zone, player, b['name'], b['side'], b['quantity'], b['price'], int(b['h_start']), int(b['h_end']),
             b.get('parent_name') or None, b.get('excl_group') or None, now))
    conn.commit()
    conn.close()


def delete_block_orders(zone, player):
    conn = get_conn()
    conn.execute("DELETE FROM block_orders WHERE zone=? AND player=?", (zone, player))
    conn.commit()
    conn.close()


def get_all_blocks():
    return _rows("SELECT * FROM block_orders ORDER BY zone, player, id")


def get_zone_blocks(zone, player=None):
    if player is None:
        return _rows("SELECT * FROM block_orders WHERE zone=? ORDER BY id", (zone,))
    return _rows("SELECT * FROM block_orders WHERE zone=? AND player=? ORDER BY id", (zone, player))


# ── Conditions de revenu minimum (MIC) ────────────────────────────
def save_mic_conditions(zone, player, conditions):
    """conditions : liste de dicts {actor, fixed_term, variable_term} ; remplace celles du trader."""
    conn = get_conn()
    conn.execute("DELETE FROM mic_conditions WHERE zone=? AND player=?", (zone, player))
    now = datetime.now().isoformat()
    for m in conditions:
        conn.execute("INSERT INTO mic_conditions (zone,player,actor,fixed_term,variable_term,submitted_at) VALUES (?,?,?,?,?,?)",
                     (zone, player, m['actor'], float(m.get('fixed_term') or 0), float(m.get('variable_term') or 0), now))
    conn.commit()
    conn.close()


def get_all_mic():
    return _rows("SELECT * FROM mic_conditions ORDER BY zone, player, id")


def get_zone_mic(zone, player=None):
    if player is None:
        return _rows("SELECT * FROM mic_conditions WHERE zone=? ORDER BY id", (zone,))
    return _rows("SELECT * FROM mic_conditions WHERE zone=? AND player=? ORDER BY id", (zone, player))


# ── NTC modifiables ───────────────────────────────────────────────
def get_ntc():
    """{(u, v): MW} définies par l'administrateur ; {} si aucune (le moteur utilise alors les valeurs par défaut)."""
    return {(r['u'], r['v']): float(r['mw']) for r in _rows("SELECT u, v, mw FROM ntc")}


def set_ntc(values):
    """values : {(u, v): MW}. Remplace l'ensemble des valeurs personnalisées."""
    conn = get_conn()
    conn.execute("DELETE FROM ntc")
    for (u, v), mw in values.items():
        conn.execute("INSERT INTO ntc (u, v, mw) VALUES (?,?,?)", (u, v, float(mw)))
    conn.commit()
    conn.close()


def reset_ntc():
    conn = get_conn()
    conn.execute("DELETE FROM ntc")
    conn.commit()
    conn.close()


# ── Résultats ─────────────────────────────────────────────────────
def save_results(welfare, volume, prices, flows, dispatch, summary):
    conn = get_conn()
    conn.execute("DELETE FROM results")
    conn.execute(
        "INSERT INTO results (run_at,welfare,volume,prices_json,flows_json,dispatch_json,summary_json) VALUES (?,?,?,?,?,?,?)",
        (datetime.now().isoformat(), float(welfare), float(volume),
         json.dumps(prices), json.dumps(flows), json.dumps(dispatch), json.dumps(summary, default=float)))
    conn.execute("UPDATE session SET value='cleared' WHERE key='phase'")
    conn.commit()
    conn.close()


def get_results():
    conn = get_conn()
    row = conn.execute("SELECT * FROM results ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if row is None:
        return None
    r = dict(row)
    r['prices']   = json.loads(r['prices_json'])
    r['flows']    = json.loads(r['flows_json'])
    r['dispatch'] = json.loads(r['dispatch_json'])
    r['summary']  = json.loads(r['summary_json'])
    return r


# Initialisation à l'import
init_db()
