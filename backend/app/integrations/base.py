from abc import ABC, abstractmethod

from pydantic import BaseModel


class PlayerDTO(BaseModel):
    external_id: str
    full_name: str
    position: str | None = None
    mlb_team: str | None = None
    status: str | None = None
    injury_status: str | None = None


class TeamDTO(BaseModel):
    external_id: str
    team_name: str
    owner_display_name: str | None = None
    is_my_team: bool = False


class RosterSlotDTO(BaseModel):
    player_external_id: str
    full_name: str
    position: str | None = None
    mlb_team: str | None = None
    slot: str | None = None


class RosterDTO(BaseModel):
    team_external_id: str
    slots: list[RosterSlotDTO] = []


class LeagueDTO(BaseModel):
    external_id: str
    season: str
    name: str
    scoring_type: str | None = None
    num_teams: int | None = None
    roster_positions: list[str] = []
    teams: list[TeamDTO] = []


class StandingsRowDTO(BaseModel):
    team_external_id: str
    wins: int | None = None
    losses: int | None = None
    ties: int | None = None
    rank: int | None = None


class PlatformAdapter(ABC):
    """Common interface any league-platform integration implements.
    Everything above this layer (sync service, API routes, frontend) is
    written against these DTOs, never a platform's raw HTML/JSON shape --
    same design intent as the sibling NFL app's app/integrations/base.py,
    kept here even with only one real implementation (CBS) today so a
    second MLB platform (Yahoo/ESPN both have real, documented APIs,
    unlike CBS) only ever touches its own package later.

    No week/matchup methods in V1 -- MLB's scoring (points or rotisserie
    over a date range, not a single weekly head-to-head game the way the
    NFL app models it) isn't modeled yet; see the project plan's Phase 2.
    """

    @abstractmethod
    def get_league(self, platform_league_id: str) -> LeagueDTO: ...

    @abstractmethod
    def get_rosters(self, platform_league_id: str) -> list[RosterDTO]: ...

    @abstractmethod
    def get_standings(self, platform_league_id: str) -> list[StandingsRowDTO]: ...

    @abstractmethod
    def get_players(self, platform_league_id: str) -> list[PlayerDTO]: ...
