"""MLB Pipeline's prospect rankings -- public, no-login page, same
"server can fetch this one directly" category as cbs_baseball_rankings.py.
Mike asked for prospects "unlisted on CBS" specifically because CBS's own
player database only has players CBS has bothered to add (established MLB
players, basically) -- a top prospect who hasn't debuted yet is often
nowhere in CBS's pool at all, so this is a different data source entirely,
not something the CBS mapper could ever surface.

BEST EFFORT, UNVERIFIED (see this project's standing rule on that, restated
in cbs_baseball_rankings.py): this sandbox's network policy blocked every
outbound host while building this, including mlb.com, so none of the
selectors below were checked against a real response. mlb.com's current
site is a Next.js app, so two extraction strategies are tried in order:

1. A `<script id="__NEXT_DATA__">` JSON blob (how Next.js ships page data
   server-side) -- searched recursively for a list of dicts that look like
   prospect rows, rather than hard-coding an exact key path that a build
   can move.
2. A plain server-rendered table, in case the page doesn't use that blob.

If a user reports this returning zero rows or a 502, check a direct
browser request to _URL and adjust whichever strategy is closer to right
-- same "look at the real thing before guessing again" process this
project already applies to the CBS mapper.
"""

import json
import re

import httpx
from bs4 import BeautifulSoup

REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MLBFantasyHQ/0.1; +https://github.com)"}
REQUEST_TIMEOUT = 20.0
_URL = "https://www.mlb.com/prospects/stats"
_RANK_KEYS = ("rank", "prospectRank", "overallRank")
_NAME_KEYS = ("fullName", "name", "playerName")
_POSITION_KEYS = ("position", "primaryPosition", "pos")
_TEAM_KEYS = ("team", "orgName", "organization", "club")
_LEVEL_KEYS = ("level", "currentLevel", "minorLeagueLevel")


class ProspectRow:
    def __init__(self, rank: int, full_name: str, position: str | None, org: str | None, level: str | None) -> None:
        self.rank = rank
        self.full_name = full_name
        self.position = position
        self.org = org
        self.level = level


def _first(d: dict, keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = d.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = value.get("name") or value.get("abbreviation")
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
    return None


def _walk_for_rows(node, found: list[dict]) -> None:
    if isinstance(node, dict):
        has_rank = any(k in node for k in _RANK_KEYS)
        has_name = any(k in node for k in _NAME_KEYS)
        if has_rank and has_name:
            found.append(node)
            return
        for value in node.values():
            _walk_for_rows(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk_for_rows(item, found)


def _rows_from_next_data(soup: BeautifulSoup) -> list[dict]:
    script = soup.select_one('script#__NEXT_DATA__[type="application/json"]')
    if script is None or not script.string:
        return []
    try:
        data = json.loads(script.string)
    except json.JSONDecodeError:
        return []
    found: list[dict] = []
    _walk_for_rows(data, found)
    return found


def _rows_from_table(soup: BeautifulSoup) -> list[dict]:
    rows: list[dict] = []
    for table in soup.select("table"):
        for tr in table.select("tbody tr"):
            cells = [c.get_text(strip=True) for c in tr.select("td")]
            if len(cells) < 2 or not cells[0].isdigit():
                continue
            rows.append(
                {
                    "rank": int(cells[0]),
                    "fullName": cells[1],
                    "position": cells[2] if len(cells) > 2 else None,
                    "team": cells[3] if len(cells) > 3 else None,
                    "level": cells[4] if len(cells) > 4 else None,
                }
            )
    return rows


def fetch_top_prospects(limit: int = 100) -> list[ProspectRow]:
    resp = httpx.get(_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    raw_rows = _rows_from_next_data(soup) or _rows_from_table(soup)
    if not raw_rows:
        raise ValueError("MLB Pipeline prospects: no recognizable prospect list found in the page")

    rows: list[ProspectRow] = []
    for raw in raw_rows:
        rank_value = next((raw.get(k) for k in _RANK_KEYS if raw.get(k) is not None), None)
        name = _first(raw, _NAME_KEYS)
        if rank_value is None or not name:
            continue
        rank = int(rank_value) if not isinstance(rank_value, str) else int(re.sub(r"\D", "", rank_value) or 0)
        if not rank:
            continue
        rows.append(
            ProspectRow(
                rank=rank,
                full_name=name,
                position=_first(raw, _POSITION_KEYS),
                org=_first(raw, _TEAM_KEYS),
                level=_first(raw, _LEVEL_KEYS),
            )
        )

    if not rows:
        raise ValueError("MLB Pipeline prospects: parsed zero usable rows")
    rows.sort(key=lambda r: r.rank)
    return rows[:limit]
