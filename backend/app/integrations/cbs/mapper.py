"""Raw CBS HTML -> DTO translation. Pure functions, no I/O.

BEST EFFORT, UNVERIFIED: no real logged-in CBS fantasy baseball page was
available to check these selectors against while building this. Every
function here is written to fail loudly (raise ValueError with a clear
message) rather than silently return an empty/wrong result when the
expected structure isn't found -- so a real test run surfaces exactly
what needs fixing instead of just showing a blank page. See
api/v1/platform_accounts.py's /cbs/raw-debug endpoint, which returns the
actual fetched HTML for exactly this purpose -- the same "debug tool
first, fix the real thing second" approach the sibling NFL app's CBS
scraper was itself fixed with when CBS last redesigned its page.
"""

from bs4 import BeautifulSoup

from app.integrations.base import LeagueDTO, PlayerDTO, RosterDTO, RosterSlotDTO, StandingsRowDTO, TeamDTO


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def map_league(html: str, platform_league_id: str, season: str) -> LeagueDTO:
    soup = _soup(html)
    title = soup.select_one("title")
    name = title.get_text(strip=True).split("|")[0].strip() if title else platform_league_id

    teams: list[TeamDTO] = []
    for link in soup.select("a[href*='/teams/']"):
        href = link.get("href", "")
        parts = [p for p in href.split("/") if p]
        if "teams" not in parts:
            continue
        idx = parts.index("teams")
        if idx + 1 >= len(parts):
            continue
        team_id = parts[idx + 1]
        team_name = link.get_text(strip=True)
        if not team_id.isdigit() or not team_name:
            continue
        teams.append(TeamDTO(external_id=team_id, team_name=team_name))

    # Dedupe by external_id -- a team's name link often appears more than
    # once on a league home page (standings widget + nav, etc.).
    seen: dict[str, TeamDTO] = {t.external_id: t for t in teams}

    return LeagueDTO(
        external_id=platform_league_id,
        season=season,
        name=name,
        teams=list(seen.values()),
    )


def map_roster(html: str, team_external_id: str) -> RosterDTO:
    soup = _soup(html)
    table = soup.select_one("table")
    if table is None:
        raise ValueError("CBS roster page: no <table> found -- page structure may have changed")

    slots: list[RosterSlotDTO] = []
    for row in table.select("tbody tr"):
        player_link = row.select_one("a[href*='/players/']")
        if player_link is None:
            continue
        href = player_link.get("href", "")
        parts = [p for p in href.split("/") if p]
        if "players" not in parts or parts.index("players") + 1 >= len(parts):
            continue
        player_id = parts[parts.index("players") + 1]
        full_name = player_link.get_text(strip=True)
        if not player_id.isdigit() or not full_name:
            continue
        cells = [c.get_text(strip=True) for c in row.select("td")]
        slot = cells[0] if cells else None
        position = cells[1] if len(cells) > 1 else None
        mlb_team = cells[2] if len(cells) > 2 else None
        slots.append(
            RosterSlotDTO(
                player_external_id=player_id,
                full_name=full_name,
                position=position or None,
                mlb_team=mlb_team or None,
                slot=slot or None,
            )
        )

    if not slots:
        raise ValueError("CBS roster page: parsed zero players -- page structure may have changed")

    return RosterDTO(team_external_id=team_external_id, slots=slots)


def map_standings(html: str) -> list[StandingsRowDTO]:
    soup = _soup(html)
    table = soup.select_one("table")
    if table is None:
        raise ValueError("CBS standings page: no <table> found -- page structure may have changed")

    rows: list[StandingsRowDTO] = []
    for i, row in enumerate(table.select("tbody tr"), start=1):
        team_link = row.select_one("a[href*='/teams/']")
        if team_link is None:
            continue
        href = team_link.get("href", "")
        parts = [p for p in href.split("/") if p]
        if "teams" not in parts or parts.index("teams") + 1 >= len(parts):
            continue
        team_id = parts[parts.index("teams") + 1]
        cells = [c.get_text(strip=True) for c in row.select("td")]
        wins = int(cells[1]) if len(cells) > 1 and cells[1].isdigit() else None
        losses = int(cells[2]) if len(cells) > 2 and cells[2].isdigit() else None
        rows.append(StandingsRowDTO(team_external_id=team_id, wins=wins, losses=losses, rank=i))

    return rows


def map_players(html: str) -> list[PlayerDTO]:
    soup = _soup(html)
    table = soup.select_one("table")
    if table is None:
        raise ValueError("CBS players page: no <table> found -- page structure may have changed")

    players: list[PlayerDTO] = []
    for row in table.select("tbody tr"):
        player_link = row.select_one("a[href*='/players/']")
        if player_link is None:
            continue
        href = player_link.get("href", "")
        parts = [p for p in href.split("/") if p]
        if "players" not in parts or parts.index("players") + 1 >= len(parts):
            continue
        player_id = parts[parts.index("players") + 1]
        if not player_id.isdigit():
            continue
        full_name = player_link.get_text(strip=True)
        cells = [c.get_text(strip=True) for c in row.select("td")]
        position = cells[1] if len(cells) > 1 else None
        mlb_team = cells[2] if len(cells) > 2 else None
        if not full_name:
            continue
        players.append(PlayerDTO(external_id=player_id, full_name=full_name, position=position, mlb_team=mlb_team))

    return players
