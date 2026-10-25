import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import League, LeagueLink, PlatformAccount, PlayerStat, Roster, RosterPlayer, Team, User
from app.schemas.league import LeagueRead, StandingsRowRead
from app.schemas.player import PlayerStatRead, RosterPlayerRead
from app.services import league_sync_service

router = APIRouter(prefix="/leagues", tags=["leagues"])

_CURRENT_SEASON = "2026"


def _get_linked_league(db: Session, league_id: uuid.UUID, user: User) -> tuple[League, PlatformAccount]:
    link = (
        db.query(LeagueLink)
        .filter(LeagueLink.league_id == league_id, LeagueLink.user_id == user.id)
        .first()
    )
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="League not found")
    return link.league, link.platform_account


@router.get("", response_model=list[LeagueRead])
def list_leagues(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[LeagueRead]:
    links = db.query(LeagueLink).filter(LeagueLink.user_id == current_user.id).all()
    return [
        LeagueRead(
            id=link.league.id,
            name=link.league.name,
            season=link.league.season,
            scoring_type=link.league.scoring_type,
            num_teams=link.league.num_teams,
            roster_positions=link.league.roster_positions,
            last_synced_at=link.league.last_synced_at,
        )
        for link in links
    ]


@router.post("/{league_id}/sync", response_model=LeagueRead)
def sync_league(
    league_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> LeagueRead:
    """Re-runs the mapper against whatever HTML the bookmarklet already
    ingested (live server-side fetches to CBS are blocked -- see
    integrations/cbs/client.py), useful after a mapper fix without
    needing the user to click the bookmarklet again."""
    league, platform_account = _get_linked_league(db, league_id, current_user)
    ingested = platform_account.extra_data.get("ingested") or {}
    if not ingested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No CBS page ingested yet -- use the bookmarklet from Settings first",
        )
    errors = []
    for page, entry in ingested.items():
        try:
            league_sync_service.ingest_page(db, current_user.id, platform_account, league.season, page, entry["html"])
        except Exception as exc:
            errors.append(f"{page}: {exc}")
    db.refresh(league)
    if errors and not league.last_synced_at:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="; ".join(errors))
    return LeagueRead(
        id=league.id,
        name=league.name,
        season=league.season,
        scoring_type=league.scoring_type,
        num_teams=league.num_teams,
        roster_positions=league.roster_positions,
        last_synced_at=league.last_synced_at,
    )


@router.get("/{league_id}/roster", response_model=list[RosterPlayerRead])
def get_my_roster(
    league_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[RosterPlayerRead]:
    league, _ = _get_linked_league(db, league_id, current_user)
    my_team = db.query(Team).filter(Team.league_id == league.id, Team.is_my_team.is_(True)).first()
    if my_team is None:
        return []
    roster = db.query(Roster).filter(Roster.team_id == my_team.id, Roster.week.is_(None)).first()
    if roster is None:
        return []

    result: list[RosterPlayerRead] = []
    for rp in roster.roster_players:
        player = rp.player
        stat = (
            db.query(PlayerStat)
            .filter(PlayerStat.player_id == player.id, PlayerStat.season == league.season)
            .first()
        )
        result.append(
            RosterPlayerRead(
                player_id=player.id,
                full_name=player.full_name,
                position=player.position,
                mlb_team=player.mlb_team,
                status=player.status,
                injury_status=player.injury_status,
                slot=rp.slot,
                stat=PlayerStatRead.model_validate(stat, from_attributes=True) if stat else None,
            )
        )
    return result


@router.get("/{league_id}/standings", response_model=list[StandingsRowRead])
def get_standings(
    league_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[StandingsRowRead]:
    league, platform_account = _get_linked_league(db, league_id, current_user)
    rows = league_sync_service.get_cached_standings(league, platform_account)
    return [StandingsRowRead(**row) for row in rows]
