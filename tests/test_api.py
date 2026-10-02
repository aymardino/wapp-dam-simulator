"""End-to-end API flow: room creation, participants, orders, rules, NTC, clearing, results, permissions."""
import os, sys, tempfile
os.environ['WAPP_API_DATABASE_URL'] = 'sqlite:///' + os.path.join(tempfile.mkdtemp(), 'rooms_test.db')
os.environ['WAPP_DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'legacy_test.db')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
API = '/api/v1'


@pytest.fixture(scope='module')
def room():
    r = client.post(API + '/rooms', json={'name': 'Formation SENELEC', 'trainer_name': 'Tamsir', 'lang': 'fr'})
    assert r.status_code == 201, r.text
    data = r.json()
    assert len(data['code']) == 6 and data['phase'] == 'submission' and data['trainer_token']
    return data


def _auth(token):
    return {'Authorization': f'Bearer {token}'}


def test_reference():
    r = client.get(API + '/reference')
    assert r.status_code == 200
    d = r.json()
    assert len(d['zones']) == 14 and len(d['lines']) == 15 and d['price_bounds'] == [0, 500]
    assert len(d['reference_supply']) == 64 and len(d['reference_demand']) == 44


def test_join_and_orders(room):
    code = room['code']
    r = client.post(API + f'/rooms/{code}/join', json={'name': 'SENELEC', 'zone': 'SEN'})
    assert r.status_code == 201, r.text
    trader = r.json()
    assert trader['role'] == 'trader' and trader['token']
    room['trader_token'] = trader['token']
    # a trader without a zone is refused
    assert client.post(API + f'/rooms/{code}/join', json={'name': 'X'}).status_code == 422
    # a second trader in the same zone is accepted
    r2 = client.post(API + f'/rooms/{code}/join', json={'name': 'OMVS Manantali', 'zone': 'SEN'})
    assert r2.status_code == 201
    room['trader2_token'] = r2.json()['token']
    book = {
        'supply': [{'actor': 'SENELEC Thermal', 'segment': 0, 'quantity': 200, 'price': 100, 'profile': 'baseload'}],
        'demand': [{'actor': 'SENELEC Demand', 'segment': 0, 'quantity': 350, 'price': 200}],
        'blocks': [{'name': 'Base nuit', 'side': 'S', 'quantity': 50, 'price': 40, 'h_start': 0, 'h_end': 5}],
        'mic': [{'actor': 'SENELEC Thermal', 'fixed_term': 1000, 'variable_term': 0}],
    }
    r = client.put(API + f'/rooms/{code}/orders/me', json=book, headers=_auth(trader['token']))
    assert r.status_code == 200, r.text
    assert len(r.json()['supply']) == 1 and r.json()['blocks'][0]['name'] == 'Base nuit'
    r = client.put(API + f'/rooms/{code}/orders/me', json={'supply': [{'actor': 'Manantali', 'quantity': 100, 'price': 32, 'profile': 'hydro'}]},
                   headers=_auth(room['trader2_token']))
    assert r.status_code == 200
    # out-of-bounds price refused by the schema
    bad = {'supply': [{'actor': 'A', 'quantity': 10, 'price': 600}]}
    assert client.put(API + f'/rooms/{code}/orders/me', json=bad, headers=_auth(trader['token'])).status_code == 422
    # without a token
    assert client.get(API + f'/rooms/{code}/orders/me').status_code == 401
    info = client.get(API + f'/rooms/{code}').json()
    assert info['counts'] == {'supply': 2, 'demand': 1, 'blocks': 1, 'mic': 1}
    assert len(info['participants']) == 3


def test_trainer_settings_and_ntc(room):
    code, tok = room['code'], room['trainer_token']
    # a trader cannot change the rules
    assert client.put(API + f'/rooms/{code}/settings', json={'tie_rule': 'order'}, headers=_auth(room['trader_token'])).status_code == 403
    r = client.put(API + f'/rooms/{code}/settings', json={'hours': [19], 'tie_rule': 'order', 'currency': 'XOF'}, headers=_auth(tok))
    assert r.status_code == 200 and r.json()['hours'] == [19] and r.json()['tie_rule'] == 'order'
    assert client.put(API + f'/rooms/{code}/settings', json={'hours': [25]}, headers=_auth(tok)).status_code == 422
    # capacities: those of the room's scenario (2024 by default), overridden line by line
    r = client.put(API + f'/rooms/{code}/ntc', json={'values': {'SEN->MLI': 0}}, headers=_auth(tok))
    assert r.status_code == 200 and r.json()['SEN->MLI'] == 0 and r.json()['NGA->BEN'] == 200
    client.put(API + f'/rooms/{code}/settings', json={'scenario': 'reference'}, headers=_auth(tok))
    r = client.get(API + f'/rooms/{code}').json()
    assert r['ntc']['NGA->BEN'] == 800 and r['ntc']['SEN->MLI'] == 0 and r['ntc_default']['SEN->MLI'] > 0
    assert client.put(API + f'/rooms/{code}/ntc', json={'values': {'XXX->YYY': 1}}, headers=_auth(tok)).status_code == 422


def test_clearing_and_results(room):
    code, tok = room['code'], room['trainer_token']
    assert client.post(API + f'/rooms/{code}/clearing', headers=_auth(room['trader_token'])).status_code == 403
    r = client.post(API + f'/rooms/{code}/clearing', headers=_auth(tok))
    assert r.status_code == 201, r.text
    run = r.json()
    assert run['welfare'] > 0 and run['result']['summary']['hours'] == [19]
    d = run['result']['summary']['diagnostics']
    assert d['pro'] == 0 and d['pao'] == 0 and d['tie_rule'] == 'order'
    assert 'SEN' in run['result']['prices'] and run['result']['summary']['n_blocks'] == 1
    assert client.get(API + f'/rooms/{code}').json()['phase'] == 'cleared'
    # submission is closed
    assert client.put(API + f'/rooms/{code}/orders/me', json={'supply': []}, headers=_auth(room['trader_token'])).status_code == 409
    r = client.get(API + f'/rooms/{code}/results')
    assert r.status_code == 200 and len(r.json()) == 1
    r = client.get(API + f'/rooms/{code}/results/latest')
    assert r.status_code == 200 and r.json()['id'] == run['id']
    r = client.get(API + f'/rooms/{code}/results/latest/me', headers=_auth(room['trader_token']))
    assert r.status_code == 200, r.text
    mine = r.json()
    assert mine['participant']['name'] == 'SENELEC' and set(mine['zone_prices'].keys()) == {'19'}
    assert {a['actor'] for a in mine['actors']} >= {'SENELEC Thermal', 'SENELEC Demand'}
    assert mine['currency'] == 'XOF' and mine['mic'][0]['actor'] == 'SENELEC Thermal'
    # reopening then a new clearing: history of 2
    assert client.put(API + f'/rooms/{code}/phase', json={'phase': 'submission'}, headers=_auth(tok)).status_code == 200
    assert client.post(API + f'/rooms/{code}/clearing', headers=_auth(tok)).status_code == 201
    assert len(client.get(API + f'/rooms/{code}/results').json()) == 2


def test_unknown_room():
    assert client.get(API + '/rooms/ZZZZZZ').status_code == 404


def test_empty_room_without_fill_is_refused():
    r = client.post(API + '/rooms', json={'name': 'Vide', 'trainer_name': 'T'}); code, tok = r.json()['code'], r.json()['trainer_token']
    assert client.put(API + f'/rooms/{code}/settings', json={'fill_mode': 'none'}, headers=_auth(tok)).status_code == 200
    r = client.post(API + f'/rooms/{code}/clearing', headers=_auth(tok))
    assert r.status_code == 422 and 'No order' in r.json()['detail']
    assert client.put(API + f'/rooms/{code}/settings', json={'fill_mode': 'zones'}, headers=_auth(tok)).status_code == 200
    r = client.post(API + f'/rooms/{code}/clearing', headers=_auth(tok))
    assert r.status_code == 201 and len(r.json()['result']['summary']['reference_zones']) == 14


def test_scenarios_and_csv_export(room):
    code, tok = room['code'], room['trainer_token']
    sc = client.get(API + '/scenarios?lang=en').json()
    keys = [x['key'] for x in sc]
    assert keys[0] == 'reference_2024' and 'reference' not in keys and 'secheresse_hydro' in keys   # Deliverable 2 set hidden
    assert next(x for x in sc if x['key'] == 'secheresse_hydro')['name'] == 'Hydro drought'
    assert client.put(API + f'/rooms/{code}/settings', json={'scenario': 'inconnu'}, headers=_auth(tok)).status_code == 422
    r = client.put(API + f'/rooms/{code}/settings', json={'scenario': 'ligne_nga_ben', 'fill_missing': True}, headers=_auth(tok))
    assert r.status_code == 200 and r.json()['scenario'] == 'ligne_nga_ben'
    assert client.get(API + f'/rooms/{code}').json()['ntc']['NGA->BEN'] == 0
    run = client.post(API + f'/rooms/{code}/clearing', headers=_auth(tok)).json()
    assert all(v == 0 for v in run['result']['flows']['NGA->BEN'].values())
    csv = client.get(API + f"/rooms/{code}/results/{run['id']}/prices.csv")
    assert csv.status_code == 200 and csv.text.splitlines()[0].startswith('hour,NGA') and len(csv.text.splitlines()) == 2
    client.put(API + f'/rooms/{code}/settings', json={'scenario': 'reference'}, headers=_auth(tok))


def test_events_stream_first_message(room):
    code = room['code']
    r = client.get(API + f'/rooms/{code}/events?once=true')
    assert r.status_code == 200 and r.headers['content-type'].startswith('text/event-stream')
    assert r.text.startswith('event: state') and '"code": "' + code + '"' in r.text


def test_room_quota_per_ip():
    from api import main as m
    old = m.MAX_ROOMS_PER_IP_PER_DAY; m.MAX_ROOMS_PER_IP_PER_DAY = 2; m._room_creations.clear()
    try:
        assert client.post(API + '/rooms', json={'name': 'a'}).status_code == 201
        assert client.post(API + '/rooms', json={'name': 'b'}).status_code == 201
        assert client.post(API + '/rooms', json={'name': 'c'}).status_code == 429
    finally:
        m.MAX_ROOMS_PER_IP_PER_DAY = old; m._room_creations.clear()


def test_purge_old_rooms():
    from datetime import datetime, timedelta
    from api.storage import SessionLocal, Room, purge_old_rooms
    db = SessionLocal()
    r = Room(id='old-room', code='OLDOLD', name='vieille'); r.settings = {}; r.created_at = datetime.utcnow() - timedelta(days=60)
    db.add(r); db.commit()
    assert purge_old_rooms(db, 30) == 1
    assert client.get(API + '/rooms/OLDOLD').status_code == 404
    db.close()


def test_duplicate_name_refused_and_participant_removal():
    r = client.post(API + '/rooms', json={'name': 'Noms'}); code, tok = r.json()['code'], r.json()['trainer_token']
    a = client.post(API + f'/rooms/{code}/join', json={'name': 'CEB', 'zone': 'TGO'}); assert a.status_code == 201
    assert client.post(API + f'/rooms/{code}/join', json={'name': ' ceb ', 'zone': 'BEN'}).status_code == 422
    assert client.post(API + f'/rooms/{code}/join', json={'name': '   ', 'zone': 'BEN'}).status_code == 422
    client.put(API + f'/rooms/{code}/orders/me', json={'supply': [{'actor': 'X', 'quantity': 10, 'price': 10}]}, headers=_auth(a.json()['token']))
    assert client.get(API + f'/rooms/{code}').json()['counts']['supply'] == 1
    assert client.delete(API + f"/rooms/{code}/participants/{a.json()['id']}", headers=_auth(a.json()['token'])).status_code == 403
    assert client.delete(API + f"/rooms/{code}/participants/{a.json()['id']}", headers=_auth(tok)).status_code == 204
    info = client.get(API + f'/rooms/{code}').json()
    assert info['counts']['supply'] == 0 and all(p['role'] == 'trainer' for p in info['participants'])
    assert client.get(API + f'/rooms/{code}/orders/me', headers=_auth(a.json()['token'])).status_code == 401
    assert 'SENELEC' in client.get(API + '/reference').json()['organisations']['SEN']


def test_fill_mode_actors_in_room():
    r = client.post(API + '/rooms', json={'name': 'Fond'}); code, tok = r.json()['code'], r.json()['trainer_token']
    client.put(API + f'/rooms/{code}/settings', json={'scenario': 'reference'}, headers=_auth(tok))   # actors of the Deliverable 2 set
    tr = client.post(API + f'/rooms/{code}/join', json={'name': 'CEB', 'zone': 'TGO'}).json()
    client.put(API + f'/rooms/{code}/orders/me', json={'supply': [{'actor': 'Nangbeto', 'quantity': 30, 'price': 20, 'profile': 'hydro'}]}, headers=_auth(tr['token']))
    assert client.get(API + f'/rooms/{code}').json()['settings']['fill_mode'] == 'actors'
    run = client.post(API + f'/rooms/{code}/clearing', headers=_auth(tok)).json()
    names = {(a['zone'], a['actor']) for a in run['result']['summary']['actors']}
    assert ('TGO', 'ContourGlobal') in names and ('TGO', 'CEB Nangbeto') not in names and ('TGO', 'Nangbeto') in names
    assert 'TGO' in run['result']['summary']['reference_zones']


def test_demo_endpoint_is_cached():
    r1 = client.get(API + '/demo'); assert r1.status_code == 200
    d = r1.json(); assert d['scenario'] == 'reference_2024' and len(d['hours']) == 24 and 'NGA' in d['prices'] and d['welfare'] > 0
    assert d['supply'] and d['demand'] and len(d['load']) == 24 and 'baseload' in d['profiles']
    r2 = client.get(API + '/demo'); assert r2.json()['welfare'] == d['welfare']


def test_default_scenario_is_reference_2024():
    r = client.post(API + '/rooms', json={'name': 'Défaut', 'trainer_name': 'F', 'lang': 'fr'}).json()
    assert r['settings']['scenario'] == 'reference_2024'
    assert r['ntc']['NGA->NER'] == 120 and r['ntc_default']['NGA->NER'] == 120   # 2024 capacities, not the Deliverable 2 ones (300)
    info = client.get(API + f"/rooms/{r['code']}").json()
    assert info['ntc_default']['NGA->NER'] == 120
