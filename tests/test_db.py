"""Migration of databases created by earlier versions (same table names, different columns)."""
import os, sys, sqlite3, tempfile, importlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _fresh_db_module(path):
    os.environ['WAPP_DB_PATH'] = path
    import engine.db as db
    importlib.reload(db)       # init_db() runs on the new database
    return db


def test_legacy_ntc_and_players_are_migrated():
    path = os.path.join(tempfile.mkdtemp(), 'legacy.db')
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE players (zone TEXT PRIMARY KEY, player TEXT, color TEXT, connected_at TEXT);
        INSERT INTO players VALUES ('CIV', 'CIE Distribution', '#1abc9c', '2026-04-15T11:37:56');
        CREATE TABLE ntc (zone_from TEXT NOT NULL, zone_to TEXT NOT NULL, value_mw REAL NOT NULL,
                          PRIMARY KEY (zone_from, zone_to));
        INSERT INTO ntc VALUES ('NGA', 'BEN', 800.0), ('SEN', 'MLI', 123.0);
        CREATE TABLE block_orders (foo TEXT);
        INSERT INTO block_orders VALUES ('x');
    """)
    c.commit(); c.close()

    db = _fresh_db_module(path)
    assert db.get_ntc() == {('NGA', 'BEN'): 800.0, ('SEN', 'MLI'): 123.0}
    assert db.get_players() == [dict(zone='CIV', player='CIE Distribution', color='#1abc9c', connected_at='2026-04-15T11:37:56')]
    assert db.get_all_blocks() == []
    tables = [r[0] for r in sqlite3.connect(path).execute("SELECT name FROM sqlite_master WHERE type='table'")]
    assert any(t.startswith('block_orders_legacy_') for t in tables), "l'ancienne table doit être conservée sous un autre nom"
    db.register_player('CIV', 'CI-Energies Hydro')
    assert len(db.get_players()) == 2
    db.set_ntc({('NGA', 'BEN'): 500.0}); assert db.get_ntc() == {('NGA', 'BEN'): 500.0}
    db.reset_ntc(); assert db.get_ntc() == {}


def test_init_is_idempotent():
    path = os.path.join(tempfile.mkdtemp(), 'twice.db')
    db = _fresh_db_module(path)
    db.init_db(); db.init_db()
    assert db.get_session()['phase'] == 'submission'
