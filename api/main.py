"""
API REST du simulateur Day-Ahead WAPP.

Lancement : uvicorn api.main:app --reload --port 8000
Documentation interactive : http://localhost:8000/docs

Parcours : POST /api/v1/rooms (le formateur crée une salle et reçoit son jeton) →
           POST /api/v1/rooms/{code}/join (les traders rejoignent et reçoivent un jeton) →
           PUT  /api/v1/rooms/{code}/orders/me (chaque trader dépose son carnet d'ordres) →
           POST /api/v1/rooms/{code}/clearing (le formateur lance le clearing) →
           GET  /api/v1/rooms/{code}/results/latest et /results/latest/me
Si le dossier web/dist existe (front compilé), il est servi à la racine.
"""
from __future__ import annotations
import os
from datetime import datetime
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, PlainTextResponse
import asyncio, json, time, collections
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from engine.clearing import ClearingError, LINES
from . import schemas as S
from . import service
from .storage import init_db, get_db, Room, Participant, ClearingRun, purge_old_rooms, SessionLocal
from .auth import get_room, current_participant, require_trainer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIST = os.path.join(ROOT, 'web', 'dist')

app = FastAPI(title="WAPP Day-Ahead Market Simulator API", version="2.0.0",
              description="Implémentation ouverte de référence du couplage de marché day-ahead zonal du WAPP : "
                          "salles de marché multi-participants, ordres par segments, blocs, MIC, clearing P1 → P1bis → P2.")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get('WAPP_CORS_ORIGINS', '*').split(','),
                   allow_methods=['*'], allow_headers=['*'])
init_db()
API = '/api/v1'
ROOM_TTL_DAYS = int(os.environ.get('WAPP_ROOM_TTL_DAYS', '30'))
MAX_ROOMS_PER_IP_PER_DAY = int(os.environ.get('WAPP_MAX_ROOMS_PER_IP_PER_DAY', '20'))
_room_creations: dict = collections.defaultdict(list)


@app.exception_handler(ClearingError)
async def _clearing_error(request: Request, exc: ClearingError):
    return JSONResponse(status_code=422, content={'detail': str(exc)})


def _participant_out(p: Participant):
    return S.ParticipantOut(id=p.id, name=p.name, zone=p.zone, role=p.role, joined_at=p.joined_at)


def _room_out(db: Session, room: Room):
    last = service.latest_run(db, room)
    return dict(code=room.code, name=room.name, phase=room.phase, settings=S.Settings(**room.settings),
                ntc={service.line_key(u, v): mw for (u, v), mw in service.effective_ntc(room).items()},
                ntc_default={service.line_key(u, v): mw for (u, v), mw in service.scenario_ntc(room).items()},
                participants=[_participant_out(p) for p in room.participants],
                counts=S.Counts(**service.counts(db, room)), last_run_id=last.id if last else None,
                created_at=room.created_at)


# ── Référence ─────────────────────────────────────────────────────
@app.get(API + '/health')
def health():
    return {'status': 'ok', 'time': datetime.utcnow().isoformat()}


@app.get(API + '/reference', summary="Zones, lignes, profils, règles et données de référence")
def reference():
    return service.reference()


_demo_cache: dict = {}


@app.get(API + '/demo', summary="Clearing de démonstration (scénario Référence 2024, 24 h), mis en cache pour le site")
def demo():
    if 'result' not in _demo_cache:
        from engine.clearing import run_clearing, PROF, LOAD_WA
        from engine.scenarios import scenario_rows
        sup, dem, ntc = scenario_rows('reference_2024')
        res = run_clearing(None, None, horizon=24, reference_rows=(sup, dem), ntc_override=ntc)
        s = res['summary']
        _demo_cache['result'] = {
            'scenario': 'reference_2024', 'hours': s['hours'], 'prices': res['prices'], 'flows': res['flows'],
            'ntc': s['rules']['ntc'], 'welfare': res['welfare'], 'volume': res['volume'],
            'net_pos': s['net_pos'], 'saturated_lines': sum(1 for l in s['lines'].values() if l['saturated_hours'] > 0),
            'elapsed': s['elapsed'], 'solver': s['solver'],
            'supply': [{k: r[k] for k in ('zone', 'actor', 'segment', 'quantity', 'price', 'profile')} for r in sup],
            'demand': [{k: r[k] for k in ('zone', 'actor', 'segment', 'quantity', 'price')} for r in dem],
            'profiles': {k: list(v) for k, v in PROF.items()}, 'load': list(LOAD_WA),
            'lines': {k: {'saturated_hours': v['saturated_hours']} for k, v in s['lines'].items()},
        }
    return _demo_cache['result']


@app.get(API + '/scenarios', summary="Scénarios pédagogiques disponibles")
def scenarios(lang: str = 'fr'):
    return service.scenario_list(lang if lang in ('fr', 'en') else 'fr')


# ── Salles ────────────────────────────────────────────────────────
@app.post(API + '/rooms', response_model=S.RoomCreated, status_code=201, summary="Créer une salle (formateur)")
def create_room(body: S.RoomCreate, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else 'local'
    now = time.time()
    _room_creations[ip] = [t for t in _room_creations[ip] if now - t < 86400]
    if len(_room_creations[ip]) >= MAX_ROOMS_PER_IP_PER_DAY:
        raise HTTPException(status_code=429, detail="Trop de salles créées depuis cette adresse aujourd'hui")
    _room_creations[ip].append(now)
    purge_old_rooms(db, ROOM_TTL_DAYS)
    room, trainer = service.create_room(db, body.name, body.trainer_name, body.lang)
    return S.RoomCreated(**_room_out(db, room), trainer_token=trainer.token)


@app.get(API + '/rooms/{code}', response_model=S.RoomOut, summary="État complet d'une salle")
def get_room_info(room: Room = Depends(get_room), db: Session = Depends(get_db)):
    return S.RoomOut(**_room_out(db, room))


@app.get(API + '/rooms/{code}/state', response_model=S.StateOut, summary="État léger (pour rafraîchissement)")
def get_state(room: Room = Depends(get_room), db: Session = Depends(get_db)):
    last = service.latest_run(db, room)
    return S.StateOut(code=room.code, phase=room.phase, counts=S.Counts(**service.counts(db, room)),
                      n_participants=len(room.participants), last_run_id=last.id if last else None,
                      last_run_at=last.run_at if last else None)


@app.post(API + '/rooms/{code}/join', response_model=S.JoinResponse, status_code=201, summary="Rejoindre une salle")
def join(body: S.JoinRequest, room: Room = Depends(get_room), db: Session = Depends(get_db)):
    try:
        p = service.join_room(db, room, body.name, body.zone, body.role)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return S.JoinResponse(**_participant_out(p).model_dump(), token=p.token, room_code=room.code)


@app.delete(API + '/rooms/{code}/participants/{participant_id}', status_code=204, summary="Retirer un participant et ses ordres (formateur)")
def remove_participant(participant_id: str, room: Room = Depends(get_room), _: Participant = Depends(require_trainer), db: Session = Depends(get_db)):
    if not service.remove_participant(db, room, participant_id):
        raise HTTPException(status_code=404, detail="Participant introuvable")


@app.get(API + '/rooms/{code}/me', response_model=S.ParticipantOut, summary="Qui suis-je dans cette salle ?")
def me(p: Participant = Depends(current_participant)):
    return _participant_out(p)


# ── Paramètres (formateur) ────────────────────────────────────────
@app.put(API + '/rooms/{code}/settings', response_model=S.Settings, summary="Modifier les paramètres et règles")
def update_settings(body: S.SettingsUpdate, room: Room = Depends(get_room), _: Participant = Depends(require_trainer),
                    db: Session = Depends(get_db)):
    s = room.settings
    s.update({k: v for k, v in body.model_dump().items() if v is not None})
    try:
        s = S.Settings(**s).model_dump()
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()[0].get('msg', 'paramètres invalides'))
    room.settings = s
    db.commit()
    return S.Settings(**s)


@app.put(API + '/rooms/{code}/phase', response_model=S.RoomOut, summary="Ouvrir ou clôturer la soumission")
def update_phase(body: S.PhaseUpdate, room: Room = Depends(get_room), _: Participant = Depends(require_trainer),
                 db: Session = Depends(get_db)):
    room.phase = body.phase
    db.commit()
    return S.RoomOut(**_room_out(db, room))


@app.put(API + '/rooms/{code}/ntc', response_model=dict, summary="Modifier les NTC de la salle")
def update_ntc(body: S.NtcUpdate, room: Room = Depends(get_room), _: Participant = Depends(require_trainer),
               db: Session = Depends(get_db)):
    valid = {service.line_key(u, v) for u, v, _c in LINES}
    bad = [k for k in body.values if k not in valid]
    if bad:
        raise HTTPException(status_code=422, detail=f"Lignes inconnues : {', '.join(bad)}")
    if any(v < 0 for v in body.values.values()):
        raise HTTPException(status_code=422, detail="Une NTC ne peut pas être négative")
    overrides = room.ntc_overrides
    overrides.update({k: float(v) for k, v in body.values.items()})
    room.ntc_overrides = overrides
    db.commit()
    return {service.line_key(u, v): mw for (u, v), mw in service.effective_ntc(room).items()}


@app.delete(API + '/rooms/{code}/ntc', response_model=dict, summary="Revenir aux NTC par défaut")
def reset_ntc(room: Room = Depends(get_room), _: Participant = Depends(require_trainer), db: Session = Depends(get_db)):
    room.ntc_overrides = {}
    db.commit()
    return {service.line_key(u, v): mw for (u, v), mw in service.effective_ntc(room).items()}


# ── Ordres ────────────────────────────────────────────────────────
@app.get(API + '/rooms/{code}/orders/me', response_model=S.OrderBookOut, summary="Mon carnet d'ordres")
def get_my_orders(room: Room = Depends(get_room), p: Participant = Depends(current_participant), db: Session = Depends(get_db)):
    return S.OrderBookOut(**service.order_book(db, room, p), participant=_participant_out(p))


@app.put(API + '/rooms/{code}/orders/me', response_model=S.OrderBookOut, summary="Remplacer mon carnet d'ordres")
def put_my_orders(body: S.OrderBook, room: Room = Depends(get_room), p: Participant = Depends(current_participant),
                  db: Session = Depends(get_db)):
    if p.role != 'trader':
        raise HTTPException(status_code=403, detail="Seuls les traders déposent des ordres")
    if room.phase != 'submission':
        raise HTTPException(status_code=409, detail="La soumission est clôturée")
    service.replace_orders(db, room, p, body)
    return S.OrderBookOut(**service.order_book(db, room, p), participant=_participant_out(p))


@app.get(API + '/rooms/{code}/orders', response_model=List[S.OrderBookOut], summary="Tous les carnets (formateur)")
def get_all_orders(room: Room = Depends(get_room), _: Participant = Depends(require_trainer), db: Session = Depends(get_db)):
    return [S.OrderBookOut(**service.order_book(db, room, p), participant=_participant_out(p))
            for p in room.participants if p.role == 'trader']


@app.delete(API + '/rooms/{code}/orders', status_code=204, summary="Supprimer tous les ordres (formateur)")
def delete_all_orders(room: Room = Depends(get_room), _: Participant = Depends(require_trainer), db: Session = Depends(get_db)):
    from sqlalchemy import delete
    from .storage import Order
    db.execute(delete(Order).where(Order.room_id == room.id))
    db.commit()


# ── Clearing et résultats ─────────────────────────────────────────
@app.post(API + '/rooms/{code}/clearing', response_model=S.ClearingRunOut, status_code=201, summary="Lancer le clearing (formateur)")
def run_clearing_endpoint(room: Room = Depends(get_room), _: Participant = Depends(require_trainer), db: Session = Depends(get_db)):
    run = service.run_room_clearing(db, room)
    return S.ClearingRunOut(id=run.id, run_at=run.run_at, welfare=run.welfare, volume=run.volume,
                            settings=room.settings, result=run.result)


@app.get(API + '/rooms/{code}/results', response_model=List[S.RunSummary], summary="Historique des clearings")
def list_runs(room: Room = Depends(get_room), db: Session = Depends(get_db)):
    runs = db.execute(select(ClearingRun).where(ClearingRun.room_id == room.id).order_by(ClearingRun.id.desc())).scalars()
    return [S.RunSummary(id=r.id, run_at=r.run_at, welfare=r.welfare, volume=r.volume) for r in runs]


def _run_or_404(db, room, run_id):
    if run_id == 'latest':
        run = service.latest_run(db, room)
    else:
        run = db.execute(select(ClearingRun).where(ClearingRun.room_id == room.id, ClearingRun.id == int(run_id))).scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Aucun clearing")
    return run


@app.get(API + '/rooms/{code}/results/{run_id}', response_model=S.ClearingRunOut, summary="Résultats complets d'un clearing")
def get_run(run_id: str, room: Room = Depends(get_room), db: Session = Depends(get_db)):
    run = _run_or_404(db, room, run_id)
    import json
    return S.ClearingRunOut(id=run.id, run_at=run.run_at, welfare=run.welfare, volume=run.volume,
                            settings=json.loads(run.settings_json), result=run.result)


@app.get(API + '/rooms/{code}/results/{run_id}/me', response_model=S.MyResultOut, summary="Mon résultat")
def get_my_result(run_id: str, room: Room = Depends(get_room), p: Participant = Depends(current_participant),
                  db: Session = Depends(get_db)):
    run = _run_or_404(db, room, run_id)
    return S.MyResultOut(participant=_participant_out(p), **service.my_result(run, p))


@app.get(API + '/rooms/{code}/results/{run_id}/prices.csv', summary="Prix zonaux d'un clearing en CSV")
def get_run_csv(run_id: str, room: Room = Depends(get_room), db: Session = Depends(get_db)):
    run = _run_or_404(db, room, run_id)
    return PlainTextResponse(service.prices_csv(run), media_type='text/csv',
                             headers={'Content-Disposition': f'attachment; filename="prices_{room.code}_{run.id}.csv"'})


# ── Flux d'événements (temps réel) ────────────────────────────────
@app.get(API + '/rooms/{code}/events', summary="Flux SSE : état de la salle à chaque changement")
async def room_events(room: Room = Depends(get_room), once: bool = False):
    """`once=true` : un seul état puis fin (tests, diagnostics)."""
    room_id, code = room.id, room.code

    async def gen():
        last_payload = None; last_beat = time.time()
        while True:
            db = SessionLocal()
            try:
                r = db.execute(select(Room).where(Room.id == room_id)).scalar_one_or_none()
                if r is None:
                    yield "event: gone\ndata: {}\n\n"; return
                payload = json.dumps(service.state_snapshot(db, r), default=str)
            finally:
                db.close()
            if payload != last_payload:
                last_payload = payload; last_beat = time.time()
                yield f"event: state\ndata: {payload}\n\n"
                if once:
                    return
            elif time.time() - last_beat > 15:
                last_beat = time.time()
                yield ": keep-alive\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(gen(), media_type='text/event-stream',
                             headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


# ── Front compilé (optionnel) ─────────────────────────────────────
if os.path.isdir(WEB_DIST):
    app.mount('/assets', StaticFiles(directory=os.path.join(WEB_DIST, 'assets')), name='assets')

    @app.get('/{full_path:path}', include_in_schema=False)
    def spa(full_path: str):
        candidate = os.path.join(WEB_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(WEB_DIST, 'index.html'))
