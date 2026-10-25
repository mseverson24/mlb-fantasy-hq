import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.cbs.adapter import CBSAdapter
from app.integrations.cbs.mapper import map_roster
from app.models import League, LeagueLink, Platform, Player, PlatformAccount, Roster, RosterPlayer, Team

_MY_TEAM_EXTERNAL_ID = "me"


def _adapter_for_account(platform_account: PlatformAccount, season: str) -> CBSAdapter:
    league_name = platform_account.extra_data.get("league_name")
    cookies = platform_account.extra_data.get("cookies", {})
    return CBSAdapter(league_name=league_name, season=season, cookies=cookies)


def _upsert_player(db: Session, slot) -> Player:
    player = db.query(Player).filter(Player.cbs_player_id == slot.player_external_id).first()
    if player is None:
        player = Player(cbs_player_id=slot.player_external_id, full_name=slot.full_name)
        db.add(player)
    player.full_name = slot.full_name
    player.position = slot.position or player.position
    player.mlb_team = slot.mlb_team or player.mlb_team
    return player


def sync_league(db: Session, user_id: uuid.UUID, platform_account: PlatformAccount, season: str) -> League:
    """Pulls the user's CBS league + their own roster and upserts it. Only
    "my" team's roster is synced in V1 (the /roster page CBS serves a
    logged-in user by default) -- other teams from the league home page are
    stored for standings/display context, not full roster detail."""
    league_name = platform_account.extra_data.get("league_name")
    adapter = _adapter_for_account(platform_account, season)

    league_dto = adapter.get_league(league_name)

    league = (
        db.query(League)
        .filter(League.platform == Platform.cbs, League.platform_league_id == league_name, League.season == season)
        .first()
    )
    if league is None:
        league = League(platform=Platform.cbs, platform_league_id=league_name, season=season, name=league_dto.name)
        db.add(league)
        db.flush()
    else:
        league.name = league_dto.name
    league.num_teams = len(league_dto.teams) or league.num_teams
    league.last_synced_at = datetime.now(timezone.utc)
    db.flush()

    link = (
        db.query(LeagueLink)
        .filter(LeagueLink.league_id == league.id, LeagueLink.user_id == user_id)
        .first()
    )
    if link is None:
        db.add(LeagueLink(league_id=league.id, user_id=user_id, platform_account_id=platform_account.id))

    for team_dto in league_dto.teams:
        team = (
            db.query(Team)
            .filter(Team.league_id == league.id, Team.platform_team_id == team_dto.external_id)
            .first()
        )
        if team is None:
            team = Team(league_id=league.id, platform_team_id=team_dto.external_id, name=team_dto.team_name)
            db.add(team)
        else:
            team.name = team_dto.team_name
    db.flush()

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

    roster_html = adapter.client.get_roster_html(team_id=None)
    roster_dto = map_roster(roster_html, _MY_TEAM_EXTERNAL_ID)

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

    db.commit()
    return league


def get_standings(db: Session, league: League, platform_account: PlatformAccount):
    adapter = _adapter_for_account(platform_account, league.season)
    rows = adapter.get_standings(league.platform_league_id)
    teams_by_external_id = {t.platform_team_id: t for t in league.teams}
    return [
        {
            "team_name": teams_by_external_id[r.team_external_id].name
            if r.team_external_id in teams_by_external_id
            else r.team_external_id,
            "owner_display_name": None,
            "is_my_team": teams_by_external_id.get(r.team_external_id).is_my_team
            if r.team_external_id in teams_by_external_id
            else False,
            "wins": r.wins,
            "losses": r.losses,
            "ties": r.ties,
            "rank": r.rank,
        }
        for r in rows
    ]
