from app.integrations import base as integration_base
from app.integrations.cbs import mapper
from app.integrations.cbs.client import CBSClient


class CBSAdapter(integration_base.PlatformAdapter):
    def __init__(self, league_name: str, season: str, cookies: dict[str, str]) -> None:
        self.league_name = league_name
        self.season = season
        self.client = CBSClient(league_name=league_name, cookies=cookies)

    def get_league(self, platform_league_id: str) -> integration_base.LeagueDTO:
        html = self.client.get_league_home_html()
        return mapper.map_league(html, platform_league_id, self.season)

    def get_rosters(self, platform_league_id: str) -> list[integration_base.RosterDTO]:
        league = self.get_league(platform_league_id)
        return [
            mapper.map_roster(self.client.get_roster_html(team.external_id), team.external_id)
            for team in league.teams
        ]

    def get_standings(self, platform_league_id: str) -> list[integration_base.StandingsRowDTO]:
        html = self.client.get_standings_html()
        return mapper.map_standings(html)

    def get_players(self, platform_league_id: str) -> list[integration_base.PlayerDTO]:
        html = self.client.get_players_html()
        return mapper.map_players(html)
