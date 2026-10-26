import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.integrations.cbs.mapper import map_league, map_players, map_roster, map_standings
from app.models import League, LeagueLink, Platform, Player, PlatformAccount, Roster, RosterPlayer, Team

_MY_TEAM_EXTERNAL_ID = "me"
_HTML_CACHE_CAP = 1_000_000
_PAGES = ("league", "roster", "standings", "players")


def _upsert_player(db: Session, slot) -> Player:
    player = db.query(Player).filter(Player.cbs_player_id == slot.player_external_id).first()
    if player is None:
        player = Player(cbs_player_id=slot.player_external_id, full_name=slot.full_name)
        db.add(player)
    player.full_name = slot.full_name
    player.position = slot.position or player.position
    player.mlb_team = slot.mlb_team or player.mlb_team
    return player


def _get_or_create_league(db: Session, platform_account: PlatformAccount, user_id: uuid.UUID, season: str) -> League:
    league_name = platform_account.extra_data.get("league_name")
    league = (
        db.query(League)
        .filter(League.platform == Platform.cbs, League.platform_league_id == league_name, League.season == season)
        .first()
    )
    if league is None:
        league = League(
            platform=Platform.cbs, platform_league_id=league_name, season=season, name=platform_account.display_name
        )
        db.add(league)
        db.flush()

    link = db.query(LeagueLink).filter(LeagueLink.league_id == league.id, LeagueLink.user_id == user_id).first()
    if link is None:
        db.add(LeagueLink(league_id=league.id, user_id=user_id, platform_account_id=platform_account.id))
        db.flush()

    return league


def _get_or_create_my_team(db: Session, league: League, platform_account: PlatformAccount) -> Team:
    my_team = (
        db.query(Team)
        .filter(Team.league_id == league.id, Team.platform_team_id == _MY_TEAM_EXTERNAL_ID)
        .first()
    )
    if my_team is None:
        my_team = Team(
            league_id=league.id,
            platform_team_id=_MY_TEAM_EXTERNAL_ID,
            name=platform_account.display_name or "My Team",
            is_my_team=True,
        )
        db.add(my_team)
        db.flush()
    return my_team


def _store_ingested_html(platform_account: PlatformAccount, page: str, html: str) -> None:
    if platform_account.extra_data is None:
        platform_account.extra_data = {}
    ingested = platform_account.extra_data.setdefault("ingested", {})
    ingested[page] = {
        "html": html[:_HTML_CACHE_CAP],
        "total_length": len(html),
        "at": datetime.now(timezone.utc).isoformat(),
    }
    flag_modified(platform_account, "extra_data")


def ingest_page(
    db: Session, user_id: uuid.UUID, platform_account: PlatformAccount, season: str, page: str, html: str
) -> str:
    """Parses one real, browser-rendered CBS page (posted by the
    bookmarklet) and upserts whatever it can. Always caches the raw HTML
    first, even on a parse failure, so /cbs/raw-debug can show it and the
    mapper can be corrected against real markup."""
    if page not in _PAGES:
        raise ValueError(f"Unknown page {page!r}")

    # Committed on its own, before any parsing -- a parse failure below
    # must not roll back the HTML we just cached, or /cbs/raw-debug has
    # nothing to show and the mapper can never be fixed against it.
    _store_ingested_html(platform_account, page, html)
    db.add(platform_account)
    db.commit()
    db.refresh(platform_account)

    if page == "league":
        league_dto = map_league(html, platform_account.extra_data.get("league_name"), season)
        league = _get_or_create_league(db, platform_account, user_id, season)
        league.name = league_dto.name
        league.num_teams = len(league_dto.teams) or league.num_teams
        league.last_synced_at = datetime.now(timezone.utc)
        db.flush()
        for team_dto in league_dto.teams:
            team = (
                db.query(Team)
                .filter(Team.league_id == league.id, Team.platform_team_id == team_dto.external_id)
                .first()
            )
            if team is None:
                db.add(Team(league_id=league.id, platform_team_id=team_dto.external_id, name=team_dto.team_name))
            else:
                team.name = team_dto.team_name
        db.commit()
        return f"Found league \"{league_dto.name}\" with {len(league_dto.teams)} team(s)."

    if page == "roster":
        league = _get_or_create_league(db, platform_account, user_id, season)
        my_team = _get_or_create_my_team(db, league, platform_account)
        roster_dto = map_roster(html, _MY_TEAM_EXTERNAL_ID)

        roster = db.query(Roster).filter(Roster.team_id == my_team.id, Roster.week.is_(None)).first()
        if roster is None:
            roster = Roster(team_id=my_team.id, week=None)
            db.add(roster)
            db.flush()
        else:
            db.query(RosterPlayer).filter(RosterPlayer.roster_id == roster.id).delete(synchronize_session=False)

        for slot in roster_dto.slots:
            player = _upsert_player(db, slot)
            db.flush()
            db.add(RosterPlayer(roster_id=roster.id, player_id=player.id, slot=slot.slot))
        league.last_synced_at = datetime.now(timezone.utc)
        db.commit()
        return f"Synced {len(roster_dto.slots)} roster player(s)."

    if page == "standings":
        rows = map_standings(html)
        platform_account.extra_data["standings_cache"] = [row.model_dump() for row in rows]
        flag_modified(platform_account, "extra_data")
        db.add(platform_account)
        db.commit()
        return f"Cached standings for {len(rows)} team(s)."

    # page == "players"
    players = map_players(html)
    for p in players:
        player = db.query(Player).filter(Player.cbs_player_id == p.external_id).first()
        if player is None:
            player = Player(cbs_player_id=p.external_id, full_name=p.full_name)
            db.add(player)
        player.full_name = p.full_name
        player.position = p.position or player.position
        player.mlb_team = p.mlb_team or player.mlb_team
    db.commit()
    return f"Upserted {len(players)} player(s)."


def get_cached_standings(league: League, platform_account: PlatformAccount) -> list[dict]:
    rows = platform_account.extra_data.get("standings_cache") or []
    teams_by_external_id = {t.platform_team_id: t for t in league.teams}
    result = []
    for r in rows:
        team = teams_by_external_id.get(r.get("team_external_id"))
        result.append(
            {
                "team_name": team.name if team else r.get("team_external_id"),
                "owner_display_name": None,
                "is_my_team": bool(team.is_my_team) if team else False,
                "wins": r.get("wins"),
                "losses": r.get("losses"),
                "ties": r.get("ties"),
                "rank": r.get("rank"),
            }
        )
    return result
