"""Adaptateur entre la salle de marché (API) et le moteur de clearing (engine.clearing)."""
from __future__ import annotations
import json, uuid
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from engine.clearing import run_clearing, NTC, LINES, ZONES, PROF, DEFAULT_SUPPLY_24, DEFAULT_DEMAND_24, default_rows, \
    PRICING_MODES, PAB_RULES, TIE_RULES, P_MIN, P_MAX, ALPHA, ALPHA_LINES
from .storage import Room, Participant, Order, ClearingRun, new_code, new_token, default_settings
from .scenarios_bridge import scenario_rows, scenario_list


def line_key(u, v):
    return f"{u}->{v}"


def scenario_ntc(room: Room):
    """{(u, v): MW} : capacités du scénario de la salle (valeurs par défaut du moteur, puis celles du scénario)."""
    ntc = dict(NTC)
    _, _, sc_ntc = scenario_rows(room.settings.get('scenario', 'reference_2024'), zones=[])
    ntc.update(sc_ntc)
    return ntc


def effective_ntc(room: Room):
    """{(u, v): MW} : capacités du scénario, surchargées par celles saisies dans la salle."""
    ntc = scenario_ntc(room)
    for k, mw in room.ntc_overrides.items():
        u, v = k.split('->')
        if (u, v) in ntc:
            ntc[(u, v)] = float(mw)
    return ntc


def counts(db: Session, room: Room):
    out = {'supply': 0, 'demand': 0, 'blocks': 0, 'mic': 0}
    for kind, in db.execute(select(Order.kind).where(Order.room_id == room.id)):
        out[{'supply': 'supply', 'demand': 'demand', 'block': 'blocks', 'mic': 'mic'}[kind]] += 1
    return out


def create_room(db: Session, name: str, trainer_name: str, lang: str):
    code = new_code()
    while db.execute(select(Room).where(Room.code == code)).scalar_one_or_none() is not None:
        code = new_code()
    room = Room(id=str(uuid.uuid4()), code=code, name=name, phase='submission')
    room.settings = default_settings(lang)
    db.add(room)
    trainer = Participant(id=str(uuid.uuid4()), room_id=room.id, name=trainer_name, zone=None, role='trainer', token=new_token())
    db.add(trainer)
    db.commit()
    return room, trainer


def join_room(db: Session, room: Room, name: str, zone, role: str):
    if role == 'trader' and zone not in ZONES:
        raise ValueError("Un trader doit choisir une zone")
    name = ' '.join(name.split())
    if not name:
        raise ValueError("Le nom est vide")
    if any(p.name.lower() == name.lower() for p in room.participants):
        raise ValueError(f"Le nom « {name} » est déjà utilisé dans cette salle ; choisissez-en un autre")
    p = Participant(id=str(uuid.uuid4()), room_id=room.id, name=name, zone=zone if role == 'trader' else None,
                    role=role, token=new_token())
    db.add(p)
    db.commit()
    return p


def replace_orders(db: Session, room: Room, p: Participant, book):
    db.execute(delete(Order).where(Order.room_id == room.id, Order.participant_id == p.id))
    for kind, items in (('supply', book.supply), ('demand', book.demand), ('block', book.blocks), ('mic', book.mic)):
        for item in items:
            db.add(Order(room_id=room.id, participant_id=p.id, kind=kind, payload_json=json.dumps(item.model_dump())))
    db.commit()


def order_book(db: Session, room: Room, p: Participant):
    book = {'supply': [], 'demand': [], 'blocks': [], 'mic': []}
    for o in db.execute(select(Order).where(Order.room_id == room.id, Order.participant_id == p.id).order_by(Order.id)).scalars():
        book[{'supply': 'supply', 'demand': 'demand', 'block': 'blocks', 'mic': 'mic'}[o.kind]].append(o.payload)
    return book


def engine_rows(db: Session, room: Room):
    """Ordres de la salle au format des lignes du moteur (zone et trader portés par le participant)."""
    parts = {p.id: p for p in room.participants}
    supply, demand, blocks, mic = [], [], [], []
    for o in db.execute(select(Order).where(Order.room_id == room.id).order_by(Order.id)).scalars():
        p = parts.get(o.participant_id)
        if p is None or p.zone is None:
            continue
        row = dict(o.payload, zone=p.zone, player=p.name)
        {'supply': supply, 'demand': demand, 'block': blocks, 'mic': mic}[o.kind].append(row)
    return supply, demand, blocks, mic


def run_room_clearing(db: Session, room: Room):
    s = room.settings
    supply, demand, blocks, mic = engine_rows(db, room)
    mode = s.get('fill_mode') or ('zones' if s.get('fill_missing', True) else 'none')
    if not (supply or demand or blocks) and mode == 'none':
        from engine.clearing import ClearingError
        raise ClearingError("Aucun ordre déposé dans la salle et complétion par les données de référence désactivée : rien à calculer.")
    ref_sup, ref_dem, _ = scenario_rows(s.get('scenario', 'reference_2024'))
    result = run_clearing(supply, demand, block_rows=blocks, mic_rows=mic, hours=s['hours'],
                          ntc_override=effective_ntc(room), fill_mode=mode,
                          pricing=s['pricing'], pab_rule=s['pab_rule'], tie_rule=s['tie_rule'],
                          reference_rows=(ref_sup, ref_dem))
    run = ClearingRun(room_id=room.id, settings_json=json.dumps(s), welfare=float(result['welfare']),
                      volume=float(result['volume']), result_json=json.dumps(result, default=float))
    room.phase = 'cleared'
    db.add(run)
    db.commit()
    return run


def latest_run(db: Session, room: Room):
    return db.execute(select(ClearingRun).where(ClearingRun.room_id == room.id).order_by(ClearingRun.id.desc())).scalars().first()


def my_result(run: ClearingRun, p: Participant):
    res = run.result
    summ = res['summary']
    zone = p.zone
    actors = [a for a in summ.get('actors', []) if a['zone'] == zone and a['player'] == p.name]
    blocks = [b for b in summ.get('blocks', []) if b['zone'] == zone and b.get('player') == p.name]
    mics = [m for m in summ.get('mic', []) if m['zone'] == zone and m.get('player') == p.name]
    prices = res['prices'].get(zone, {}) if zone else {}
    return dict(run_id=run.id, run_at=run.run_at, zone_prices=prices, actors=actors, blocks=blocks, mic=mics,
                hours=summ.get('hours', []), currency=json.loads(run.settings_json).get('currency', 'USD'))


def prices_csv(run: ClearingRun):
    res = run.result; hours = res['summary']['hours']; zones = list(res['prices'].keys())
    lines = ['hour,' + ','.join(zones)]
    for h in hours:
        lines.append(f"{h}," + ','.join(str(res['prices'][z][str(h)]) for z in zones))
    return '\n'.join(lines) + '\n'


def state_snapshot(db: Session, room: Room):
    last = latest_run(db, room)
    return dict(code=room.code, phase=room.phase, counts=counts(db, room), n_participants=len(room.participants),
                last_run_id=last.id if last else None, last_run_at=last.run_at.isoformat() if last else None,
                settings=room.settings)


def remove_participant(db: Session, room: Room, participant_id: str):
    p = next((x for x in room.participants if x.id == participant_id), None)
    if p is None or p.role == 'trainer':
        return False
    db.execute(delete(Order).where(Order.participant_id == p.id))
    db.delete(p)
    db.commit()
    return True


def reference():
    from engine.actors import ZONE_ACTORS, CUSTOM_SENTINEL
    sup, dem = default_rows()
    return {
        'organisations': {z: [a for a in names if a != CUSTOM_SENTINEL] for z, names in ZONE_ACTORS.items()},
        'zones': ZONES,
        'lines': [{'from': u, 'to': v, 'ntc': c} for u, v, c in LINES],
        'alpha': {'factor': ALPHA, 'lines': [line_key(u, v) for u, v in ALPHA_LINES]},
        'profiles': {k: v for k, v in PROF.items()},
        'price_bounds': [P_MIN, P_MAX],
        'rules': {'pricing': list(PRICING_MODES), 'pab_rule': list(PAB_RULES), 'tie_rule': list(TIE_RULES)},
        'reference_supply': sup,
        'reference_demand': dem,
    }
