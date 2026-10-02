"""
Persistance de l'API : salles de marché, participants, ordres, clearings (SQLAlchemy 2, SQLite par défaut).
Base distincte de celle de l'application Streamlit historique (engine/db.py).
Variable d'environnement WAPP_API_DATABASE_URL : sqlite:///chemin.db (défaut : data/rooms.db) ou URL Postgres.
"""
from __future__ import annotations
import os, json, secrets, string
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import create_engine, String, Text, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = os.environ.get('WAPP_API_DATABASE_URL') or 'sqlite:///' + os.path.join(ROOT, 'data', 'rooms.db')
if DATABASE_URL.startswith('sqlite:///'):
    os.makedirs(os.path.dirname(DATABASE_URL.replace('sqlite:///', '')) or '.', exist_ok=True)
engine = create_engine(DATABASE_URL, future=True,
                       connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def new_code(n=6):
    return ''.join(secrets.choice(CODE_ALPHABET) for _ in range(n))


def new_token():
    return secrets.token_urlsafe(24)


def default_settings(lang='fr'):
    return {
        'hours': list(range(24)),
        'pricing': 'complete',
        'pab_rule': 'euphemia',
        'tie_rule': 'prorata',
        'fill_missing': True,
        'fill_mode': 'actors',
        'currency': 'USD',
        'lang': lang,
        'market_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'scenario': 'reference_2024',
    }


class Base(DeclarativeBase):
    pass


class Room(Base):
    __tablename__ = 'rooms'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    phase: Mapped[str] = mapped_column(String(20), default='submission')
    settings_json: Mapped[str] = mapped_column(Text, default='{}')
    ntc_json: Mapped[str] = mapped_column(Text, default='{}')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    participants: Mapped[List['Participant']] = relationship('Participant', back_populates='room', cascade='all, delete-orphan')
    orders: Mapped[List['Order']] = relationship('Order', back_populates='room', cascade='all, delete-orphan')
    runs: Mapped[List['ClearingRun']] = relationship('ClearingRun', back_populates='room', cascade='all, delete-orphan')

    @property
    def settings(self):
        s = default_settings()
        s.update(json.loads(self.settings_json or '{}'))
        return s

    @settings.setter
    def settings(self, value):
        self.settings_json = json.dumps(value)

    @property
    def ntc_overrides(self):
        return {k: float(v) for k, v in json.loads(self.ntc_json or '{}').items()}

    @ntc_overrides.setter
    def ntc_overrides(self, value):
        self.ntc_json = json.dumps(value)


class Participant(Base):
    __tablename__ = 'participants'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey('rooms.id'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    zone: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    role: Mapped[str] = mapped_column(String(20))          # trainer | trader | observer
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    room: Mapped[Room] = relationship('Room', back_populates='participants')


class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[str] = mapped_column(ForeignKey('rooms.id'), index=True)
    participant_id: Mapped[str] = mapped_column(ForeignKey('participants.id'), index=True)
    kind: Mapped[str] = mapped_column(String(10))          # supply | demand | block | mic
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    room: Mapped[Room] = relationship('Room', back_populates='orders')

    @property
    def payload(self):
        return json.loads(self.payload_json)


class ClearingRun(Base):
    __tablename__ = 'clearing_runs'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[str] = mapped_column(ForeignKey('rooms.id'), index=True)
    run_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    settings_json: Mapped[str] = mapped_column(Text)
    welfare: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    result_json: Mapped[str] = mapped_column(Text)
    room: Mapped[Room] = relationship('Room', back_populates='runs')

    @property
    def result(self):
        return json.loads(self.result_json)


def init_db():
    Base.metadata.create_all(engine)


def purge_old_rooms(db, ttl_days):
    """Supprime les salles sans activité (ordres, clearings, participants) depuis plus de ttl_days jours."""
    from sqlalchemy import select, func
    if ttl_days <= 0:
        return 0
    limit = datetime.utcnow() - timedelta(days=ttl_days)
    n = 0
    for room in db.execute(select(Room).where(Room.created_at < limit)).scalars().all():
        last = max([room.created_at] + [p.joined_at for p in room.participants] + [o.created_at for o in room.orders] + [r.run_at for r in room.runs])
        if last < limit:
            db.delete(room); n += 1
    if n:
        db.commit()
    return n


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
