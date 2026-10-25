import re

import httpx
from bs4 import BeautifulSoup

REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MLBFantasyHQ/0.1; +https://github.com)"}
REQUEST_TIMEOUT = 20.0
_URL = "https://www.cbssports.com/fantasy/baseball/rankings/"
_SLUG_RE = re.compile(r"/mlb/players/\d+/([a-z0-9-]+)/")


class CBSRankingsRow:
    def __init__(self, rank: int, full_name: str, position: str | None) -> None:
        self.rank = rank
        self.full_name = full_name
        self.position = position


def _name_from_href(href: str) -> str | None:
    match = _SLUG_RE.search(href)
    if not match:
        return None
    return " ".join(part.capitalize() for part in match.group(1).split("-"))


def fetch_rankings() -> list[CBSRankingsRow]:
    """Public, no-login page -- CBS's fantasy baseball overall rankings.
    BEST EFFORT: mirrors the exact table/cell selectors already confirmed
    working for CBS's *football* rankings page in the sibling NFL app
    (app/scrapers/cbs_sports.py there), on the assumption CBS reuses the
    same site template (table.FantasyRankingsTable) across its fantasy
    sports verticals. Unverified against the real baseball page -- if this
    returns zero rows, CBS's baseball page likely uses different markup
    and this needs updating against the real HTML (see the raw-debug
    endpoint pattern used throughout this project for exactly that)."""
    resp = httpx.get(_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    table = soup.select_one("table.FantasyRankingsTable")
    if table is None:
        raise ValueError("CBS Fantasy Baseball: FantasyRankingsTable not found")
    tbody = table.select_one("tbody") or table

    rows: list[CBSRankingsRow] = []
    for row_tr in tbody.select("tr"):
        rank_td = row_tr.select_one("td.FantasyRankingsTable-td--rank")
        player_link = row_tr.select_one("a.FantasyRankingsTable-playerLink[href]")
        if rank_td is None or player_link is None:
            continue
        rank_text = rank_td.get_text(strip=True)
        if not rank_text.isdigit():
            continue
        href = player_link.get("href", "")
        name = _name_from_href(href) or player_link.get_text(strip=True)
        pos_td = row_tr.select_one("td.FantasyRankingsTable-td--pos")
        position = pos_td.get_text(strip=True) if pos_td else None
        rows.append(CBSRankingsRow(rank=int(rank_text), full_name=name, position=position))

    if not rows:
        raise ValueError("CBS Fantasy Baseball: parsed zero rows")
    return rows
