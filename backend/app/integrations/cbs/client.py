import re

import httpx

# CBS Fantasy has no public OAuth API (confirmed: its old "v3" JSON API and
# developer docs are dead -- the docs domain doesn't even resolve anymore).
# This follows the one surviving community reference
# (cbs_fantasy_sports_api_token_fetcher, a Ruby gem) for the login step:
# POST the credentials to CBS's own login page and pull a token out of the
# HTML response. From there, this client scrapes the user's own
# authenticated league pages as HTML (BeautifulSoup) -- the same technique
# this app's sibling NFL app already relies on for CBS's *public* rankings
# pages (app/scrapers/cbs_sports.py there), just now behind a login.
#
# BEST EFFORT: CBS's actual markup/endpoints for a logged-in league/roster/
# standings view aren't documented anywhere accessible today. The page
# paths below (ROSTER_PATH/STANDINGS_PATH/etc.) are reasonable guesses
# based on how CBS fantasy site URLs are conventionally structured
# (https://{league_name}.cbssports.com/...), not confirmed against a real
# account. Expect to adjust these once tested against a real login --
# see get_league/get_roster_html's docstrings for exactly what to check.

_LOGIN_URL = "https://www.cbssports.com/login"
_TOKEN_RE = re.compile(r'(?<=var token = ").+(?=")')
REQUEST_TIMEOUT = 20.0
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MLBFantasyHQ/0.1; +https://github.com)",
}


class CBSLoginError(Exception):
    pass


class CBSClient:
    """One instance per linked account. `cookies` holds the authenticated
    session (set by `login()` or restored from a stored PlatformAccount);
    every other method reuses it for authenticated page fetches."""

    def __init__(self, league_name: str, cookies: dict[str, str] | None = None) -> None:
        self.league_name = league_name
        self.cookies = cookies or {}

    def login(self, username: str, password: str) -> str:
        """Logs in once with real credentials; returns a session token.
        The password is used here only -- never stored. Raises
        CBSLoginError if CBS's response doesn't contain the expected
        token (e.g. wrong credentials, or CBS's login page markup has
        changed since this was last checked)."""
        resp = httpx.post(
            _LOGIN_URL,
            data={
                "userid": username,
                "password": password,
                "xurl": f"https://{self.league_name}.cbssports.com/",
            },
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        match = _TOKEN_RE.search(resp.text)
        if not match:
            raise CBSLoginError(
                "CBS login did not return the expected session token -- either the "
                "credentials/league name are wrong, or CBS changed its login page."
            )
        self.cookies = dict(resp.cookies)
        return match.group(0)

    def _get_html(self, path: str) -> str:
        resp = httpx.get(
            f"https://{self.league_name}.cbssports.com{path}",
            cookies=self.cookies,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        return resp.text

    def get_league_home_html(self) -> str:
        return self._get_html("/")

    def get_roster_html(self, team_id: str | None = None) -> str:
        path = f"/teams/{team_id}/roster" if team_id else "/roster"
        return self._get_html(path)

    def get_standings_html(self) -> str:
        return self._get_html("/standings")

    def get_players_html(self) -> str:
        return self._get_html("/players")
