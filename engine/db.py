"""
WAPP Market Simulator — Shared State via SQLite
All players and the admin share this DB on the LAN.
"""
import sqlite3, json, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'market.db')

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
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
            zone      TEXT PRIMARY KEY,
            player    TEXT,
            color     TEXT,
            connected_at TEXT
        );
    """)
    # Default session state
    defaults = {
        'phase': 'submission',   # submission | cleared
        'market_date': datetime.now().strftime('%Y-%m-%d'),
        'horizon': '24',         # 1 or 24
        'mode': 'multizone',     # monozone or multizone
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO session VALUES (?,?)", (k, v))
    conn.commit()
    conn.close()

# ── Session helpers ───────────────────────────────────────────────
def get_session():
    conn = get_conn()
    rows = conn.execute("SELECT key,value FROM session").fetchall()
    conn.close()
    return {r['key']: r['value'] for r in rows}

def set_session(key, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO session VALUES (?,?)", (key, str(value)))
    conn.commit()
    conn.close()

def reset_market():
    conn = get_conn()
    conn.execute("DELETE FROM supply_offers")
    conn.execute("DELETE FROM demand_bids")
    conn.execute("DELETE FROM results")
    conn.execute("UPDATE session SET value='submission' WHERE key='phase'")
    conn.commit()
    conn.close()

# ── Player registry ───────────────────────────────────────────────
ZONE_COLORS = {
    'NGA':'#e74c3c','BEN':'#e67e22','TGO':'#f1c40f','GHA':'#2ecc71',
    'CIV':'#1abc9c','BFA':'#3498db','MLI':'#9b59b6','SEN':'#ad1457',
    'GIN':'#e91e63','SLE':'#00bcd4','LBR':'#8bc34a','GNB':'#ff5722',
    'GMB':'#607d8b','NER':'#795548'
}

def register_player(zone, player_name):
    conn = get_conn()
    color = ZONE_COLORS.get(zone, '#888888')
    conn.execute(
        "INSERT OR REPLACE INTO players VALUES (?,?,?,?)",
        (zone, player_name, color, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_players():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM players ORDER BY zone").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Offer management ──────────────────────────────────────────────
def save_supply_offers(zone, player, offers):
    """offers: list of dicts {actor, segment, quantity, price, profile}"""
    conn = get_conn()
    conn.execute("DELETE FROM supply_offers WHERE zone=? AND player=?", (zone, player))
    now = datetime.now().isoformat()
    for o in offers:
        conn.execute(
            "INSERT INTO supply_offers (zone,player,actor,segment,quantity,price,profile,submitted_at) VALUES (?,?,?,?,?,?,?,?)",
            (zone, player, o['actor'], o['segment'], o['quantity'], o['price'], o.get('profile','baseload'), now)
        )
    conn.commit()
    conn.close()

def save_demand_bids(zone, player, bids):
    """bids: list of dicts {actor, segment, quantity, price}"""
    conn = get_conn()
    conn.execute("DELETE FROM demand_bids WHERE zone=? AND player=?", (zone, player))
    now = datetime.now().isoformat()
    for b in bids:
        conn.execute(
            "INSERT INTO demand_bids (zone,player,actor,segment,quantity,price,submitted_at) VALUES (?,?,?,?,?,?,?)",
            (zone, player, b['actor'], b['segment'], b['quantity'], b['price'], now)
        )
    conn.commit()
    conn.close()

def get_all_supply():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM supply_offers ORDER BY zone,price").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_demand():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM demand_bids ORDER BY zone,price DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_zone_supply(zone):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM supply_offers WHERE zone=? ORDER BY price", (zone,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_zone_demand(zone):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM demand_bids WHERE zone=? ORDER BY price DESC", (zone,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Results ───────────────────────────────────────────────────────
def save_results(welfare, volume, prices, flows, dispatch, summary):
    conn = get_conn()
    conn.execute("DELETE FROM results")
    conn.execute(
        "INSERT INTO results (run_at,welfare,volume,prices_json,flows_json,dispatch_json,summary_json) VALUES (?,?,?,?,?,?,?)",
        (datetime.now().isoformat(), welfare, volume,
         json.dumps(prices), json.dumps(flows), json.dumps(dispatch), json.dumps(summary))
    )
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


# Initialize on import
init_db()
