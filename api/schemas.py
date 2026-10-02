"""Input and output schemas of the API (pydantic v2)."""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator
from engine.clearing import ZONES, PROF, P_MIN, P_MAX, PRICING_MODES, PAB_RULES, TIE_RULES
from engine.scenarios import SCENARIOS

Zone = Literal[tuple(ZONES)]              # type: ignore[valid-type]
Profile = Literal[tuple(PROF.keys())]     # type: ignore[valid-type]
Pricing = Literal[PRICING_MODES]          # type: ignore[valid-type]
PabRule = Literal[PAB_RULES]              # type: ignore[valid-type]
TieRule = Literal[TIE_RULES]              # type: ignore[valid-type]
Lang = Literal['fr', 'en']
Scenario = Literal[tuple(SCENARIOS.keys())]   # type: ignore[valid-type]
Role = Literal['trainer', 'trader', 'observer']
Phase = Literal['submission', 'cleared']


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    trainer_name: str = Field(default='Formateur', min_length=1, max_length=120)
    lang: Lang = 'fr'


class Settings(BaseModel):
    hours: List[int] = Field(default_factory=lambda: list(range(24)))
    pricing: Pricing = 'complete'
    pab_rule: PabRule = 'euphemia'
    tie_rule: TieRule = 'prorata'
    fill_missing: bool = True
    fill_mode: Literal['none', 'zones', 'actors'] = 'actors'
    currency: str = Field(default='USD', max_length=8)
    lang: Lang = 'fr'
    market_date: str = Field(default='', max_length=10)
    scenario: Scenario = 'reference_2024'

    @field_validator('hours')
    @classmethod
    def _hours(cls, v):
        v = sorted(set(int(h) for h in v))
        if not v or any(h < 0 or h > 23 for h in v):
            raise ValueError('hours must be between 0 and 23')
        return v


class SettingsUpdate(BaseModel):
    hours: Optional[List[int]] = None
    pricing: Optional[Pricing] = None
    pab_rule: Optional[PabRule] = None
    tie_rule: Optional[TieRule] = None
    fill_missing: Optional[bool] = None
    fill_mode: Optional[Literal['none', 'zones', 'actors']] = None
    currency: Optional[str] = Field(default=None, max_length=8)
    lang: Optional[Lang] = None
    market_date: Optional[str] = Field(default=None, max_length=10)
    scenario: Optional[Scenario] = None


class PhaseUpdate(BaseModel):
    phase: Phase


class JoinRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    zone: Optional[Zone] = None
    role: Literal['trader', 'observer'] = 'trader'


class ParticipantOut(BaseModel):
    id: str
    name: str
    zone: Optional[str]
    role: Role
    joined_at: datetime


class JoinResponse(ParticipantOut):
    token: str
    room_code: str


class Counts(BaseModel):
    supply: int = 0
    demand: int = 0
    blocks: int = 0
    mic: int = 0


class RoomOut(BaseModel):
    code: str
    name: str
    phase: Phase
    settings: Settings
    ntc: Dict[str, float]
    ntc_default: Dict[str, float] = {}
    participants: List[ParticipantOut]
    counts: Counts
    last_run_id: Optional[int]
    created_at: datetime


class RoomCreated(RoomOut):
    trainer_token: str


class StateOut(BaseModel):
    code: str
    phase: Phase
    counts: Counts
    n_participants: int
    last_run_id: Optional[int]
    last_run_at: Optional[datetime]


class SupplySegment(BaseModel):
    actor: str = Field(min_length=1, max_length=120)
    segment: int = Field(default=0, ge=0, le=3)
    quantity: float = Field(ge=0)
    price: float = Field(ge=P_MIN, le=P_MAX)
    profile: Profile = 'baseload'


class DemandSegment(BaseModel):
    actor: str = Field(min_length=1, max_length=120)
    segment: int = Field(default=0, ge=0, le=3)
    quantity: float = Field(ge=0)
    price: float = Field(ge=P_MIN, le=P_MAX)


class BlockOrder(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    side: Literal['S', 'D']
    quantity: float = Field(ge=0)
    price: float = Field(ge=P_MIN, le=P_MAX)
    h_start: int = Field(default=0, ge=0, le=23)
    h_end: int = Field(default=23, ge=0, le=23)
    parent_name: Optional[str] = None
    excl_group: Optional[str] = None

    @field_validator('h_end')
    @classmethod
    def _range(cls, v, info):
        if 'h_start' in info.data and v < info.data['h_start']:
            raise ValueError('h_end must be >= h_start')
        return v


class MicCondition(BaseModel):
    actor: str = Field(min_length=1, max_length=120)
    fixed_term: float = Field(default=0, ge=0)
    variable_term: float = Field(default=0, ge=0)


class OrderBook(BaseModel):
    supply: List[SupplySegment] = Field(default_factory=list)
    demand: List[DemandSegment] = Field(default_factory=list)
    blocks: List[BlockOrder] = Field(default_factory=list)
    mic: List[MicCondition] = Field(default_factory=list)


class OrderBookOut(OrderBook):
    participant: ParticipantOut


class NtcUpdate(BaseModel):
    values: Dict[str, float] = Field(description='{"NGA->BEN": 800, ...}; lines not listed keep their current value')


class RunSummary(BaseModel):
    id: int
    run_at: datetime
    welfare: float
    volume: float


class ClearingRunOut(RunSummary):
    settings: Dict[str, Any]
    result: Dict[str, Any]


class MyResultOut(BaseModel):
    run_id: int
    run_at: datetime
    participant: ParticipantOut
    zone_prices: Dict[str, float]
    actors: List[Dict[str, Any]]
    blocks: List[Dict[str, Any]]
    mic: List[Dict[str, Any]]
    hours: List[int]
    currency: str
