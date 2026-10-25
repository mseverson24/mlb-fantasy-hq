import uuid

from pydantic import BaseModel


class PlayerStatRead(BaseModel):
    season: str
    games: int | None = None
    at_bats: int | None = None
    hits: int | None = None
    runs: int | None = None
    home_runs: int | None = None
    rbi: int | None = None
    stolen_bases: int | None = None
    batting_avg: float | None = None
    ops: float | None = None
    wins: int | None = None
    losses: int | None = None
    saves: int | None = None
    innings_pitched: float | None = None
    strikeouts: int | None = None
    era: float | None = None
    whip: float | None = None


class RosterPlayerRead(BaseModel):
    player_id: uuid.UUID
    full_name: str
    position: str | None = None
    mlb_team: str | None = None
    status: str | None = None
    injury_status: str | None = None
    slot: str | None = None
    stat: PlayerStatRead | None = None


class RankedPlayerRead(BaseModel):
    rank: int
    full_name: str
    position: str | None = None
    mlb_team: str | None = None
