import httpx

# CBS Fantasy has no public OAuth API, and no login endpoint a server can
# authenticate against either -- confirmed live: a POST of credentials to
# CBS's own /login page (the technique the one surviving community
# reference, cbs_fantasy_sports_api_token_fetcher, used against CBS's old
# 2017-era site) just returns the blank login *page* itself now, a modern
# client-side-rendered Next.js app with no server-processed form POST
# underneath it to hook into.
#
# Instead: the user logs into CBS normally in their own browser, then
# copies the resulting `auth_session` cookie (confirmed, via a real
# logged-in account's dev tools, to be CBS's actual session cookie -- every
# other cookie CBS sets is third-party analytics/ads or AWS load-balancer
# routing) into this app once. From there, this client reuses that cookie
# to scrape the user's own authenticated league pages as HTML
# (BeautifulSoup) -- the same technique this app's sibling NFL app already
# relies on for CBS's *public* rankings pages (app/scrapers/cbs_sports.py
# there), just now behind a login.
#
# Confirmed live via /platform-accounts/cbs/raw-debug against a real
# account: hitting https://{league_name}.cbssports.com/... (no sport
# segment) doesn't recognize the session and redirects to CBS's login page
# instead -- the redirect's own xurl parameter revealed the real host is
# https://{league_name}.baseball.cbssports.com/...

REQUEST_TIMEOUT = 20.0
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class CBSClient:
    """One instance per linked account. `cookies` holds the authenticated
    session (the auth_session cookie the user pasted in, restored from a
    stored PlatformAccount); every method here reuses it for authenticated
    page fetches."""

    def __init__(self, league_name: str, cookies: dict[str, str] | None = None) -> None:
        self.league_name = league_name
        self.cookies = cookies or {}

    def _get_html(self, path: str) -> str:
        resp = httpx.get(
            f"https://{self.league_name}.baseball.cbssports.com{path}",
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
