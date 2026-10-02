"""Parcours complet de l'API : création de salle, participants, ordres, règles, NTC, clearing, résultats, droits."""
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
    # un trader sans zone est refusé
    assert client.post(API + f'/rooms/{code}/join', json={'name': 'X'}).status_code == 422
    # un second trader dans la même zone est accepté
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
    # prix hors bornes refusé par le schéma
    bad = {'supply': [{'actor': 'A', 'quantity': 10, 'price': 600}]}
    assert client.put(API + f'/rooms/{code}/orders/me', json=bad, headers=_auth(trader['token'])).status_code == 422
    # sans jeton
    assert client.get(API + f'/rooms/{code}/orders/me').status_code == 401
    info = client.get(API + f'/rooms/{code}').json()
    assert info['counts'] == {'supply': 2, 'demand': 1, 'blocks': 1, 'mic': 1}
    assert len(info['participants']) == 3


def test_trainer_settings_and_ntc(room):
    code, tok = room['code'], room['trainer_token']
    # un trader ne peut pas changer les règles
    assert client.put(API + f'/rooms/{code}/settings', json={'tie_rule': 'order'}, headers=_auth(room['trader_token'])).status_code == 403
    r = client.put(API + f'/rooms/{code}/settings', json={'hours': [19], 'tie_rule': 'order', 'currency': 'XOF'}, headers=_auth(tok))
    assert r.status_code == 200 and r.json()['hours'] == [19] and r.json()['tie_rule'] == 'order'
    assert client.put(API + f'/rooms/{code}/settings', json={'hours': [25]}, headers=_auth(tok)).status_code == 422
    r = client.put(API + f'/rooms/{code}/ntc', json={'values': {'SEN->MLI': 0}}, headers=_auth(tok))
    assert r.status_code == 200 and r.json()['SEN->MLI'] == 0 and r.json()['NGA->BEN'] == 800
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
    # la soumission est fermée
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
    # réouverture puis nouveau clearing : historique de 2
    assert client.put(API + f'/rooms/{code}/phase', json={'phase': 'submission'}, headers=_auth(tok)).status_code == 200
    assert client.post(API + f'/rooms/{code}/clearing', headers=_auth(tok)).status_code == 201
    assert len(client.get(API + f'/rooms/{code}/results').json()) == 2


def test_unknown_room():
    assert client.get(API + '/rooms/ZZZZZZ').status_code == 404
