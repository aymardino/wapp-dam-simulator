"""Authentification par jeton de participant (Authorization: Bearer <token>)."""
from __future__ import annotations
from typing import Optional
from fastapi import Depends, Header, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from .storage import get_db, Room, Participant


def get_room(code: str = Path(..., min_length=4, max_length=8), db: Session = Depends(get_db)) -> Room:
    room = db.execute(select(Room).where(Room.code == code.upper())).scalar_one_or_none()
    if room is None:
        raise HTTPException(status_code=404, detail="Salle introuvable")
    return room


def current_participant(room: Room = Depends(get_room), authorization: Optional[str] = Header(default=None),
                        db: Session = Depends(get_db)) -> Participant:
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail="Jeton de participant requis")
    token = authorization.split(' ', 1)[1].strip()
    p = db.execute(select(Participant).where(Participant.token == token, Participant.room_id == room.id)).scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=401, detail="Jeton invalide pour cette salle")
    return p


def require_trainer(p: Participant = Depends(current_participant)) -> Participant:
    if p.role != 'trainer':
        raise HTTPException(status_code=403, detail="Réservé au formateur")
    return p
