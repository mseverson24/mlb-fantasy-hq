import uuid
from datetime import datetime

from pydantic import BaseModel


class LeagueRead(BaseModel):
    id: uuid.UUID
    name: str
    season: str
    scoring_type: str | None = None
    num_teams: int | None = None
    roster_positions: list[str] = []
    last_synced_at: datetime | None = None


class StandingsRowRead(BaseModel):
    team_name: str
    owner_display_name: str | None = None
    is_my_team: bool = False
    wins: int | None = None
    losses: int | None = None
    ties: int | None = None
    rank: int | None = None
