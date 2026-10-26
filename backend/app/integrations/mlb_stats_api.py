"""Live stats from MLB's own public Stats API (statsapi.mlb.com) -- no key,
no login, used by MLB.com itself. Reachable from Render's normal outbound
internet; NOT reachable from this project's dev sandbox when this was
written (its network policy blocks the host), so the exact field names
below are from the API's well-known, long-stable schema rather than a
live response captured here. BEST EFFORT, like cbs_baseball_rankings.py --
if a season comes back empty or a field is missing, check a direct browser
hit of the URLs below before assuming the matching logic is wrong.
"""

import re
import unicodedata

import httpx

REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MLBFantasyHQ/0.1; +https://github.com)"}
REQUEST_TIMEOUT = 20.0
_BASE_URL = "https://statsapi.mlb.com/api/v1/stats"
_SUFFIX_RE = re.compile(r"\s+(jr|sr|ii|iii|iv)\.?$", re.IGNORECASE)


def normalize_name(full_name: str) -> str:
    """Case/accent/punctuation-insensitive key so 'Luis Robert Jr.' (CBS)
    matches 'Luis Robert Jr' (MLB) matches 'luis robert' (either, suffix
    stripped as a last resort)."""
    decomposed = unicodedata.normalize("NFKD", full_name)
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned = re.sub(r"[.'`]", "", ascii_only).strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return _SUFFIX_RE.sub("", cleaned).strip()


def _fetch_group(season: str, group: str) -> list[dict]:
    resp = httpx.get(
        _BASE_URL,
        params={"stats": "season", "group": group, "sportId": 1, "season": season, "limit": 2000},
        headers=REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    stat_groups = data.get("stats") or []
    if not stat_groups:
        return []
    return stat_groups[0].get("splits") or []


def _hitting_row(split: dict) -> dict:
    stat = split.get("stat") or {}
    return {
        "games": stat.get("gamesPlayed"),
        "at_bats": stat.get("atBats"),
        "hits": stat.get("hits"),
        "runs": stat.get("runs"),
        "home_runs": stat.get("homeRuns"),
        "rbi": stat.get("rbi"),
        "stolen_bases": stat.get("stolenBases"),
        "batting_avg": _to_float(stat.get("avg")),
        "ops": _to_float(stat.get("ops")),
    }


def _pitching_row(split: dict) -> dict:
    stat = split.get("stat") or {}
    return {
        "games": stat.get("gamesPlayed"),
        "wins": stat.get("wins"),
        "losses": stat.get("losses"),
        "saves": stat.get("saves"),
        "innings_pitched": _to_float(stat.get("inningsPitched")),
        "strikeouts": stat.get("strikeOuts"),
        "era": _to_float(stat.get("era")),
        "whip": _to_float(stat.get("whip")),
    }


def _to_float(value) -> float | None:
    if value in (None, "", "-.--", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_season_stats_by_name(season: str) -> dict[str, dict]:
    """Returns {normalize_name(full_name): stat-dict} for every hitter and
    pitcher with a season line, merging both groups (a two-way player gets
    both sets of keys). Raises on a transport/HTTP failure; callers should
    treat that as "stats unavailable right now", not "no stats exist", and
    fall back to whatever is already cached in the DB."""
    merged: dict[str, dict] = {}
    for group, row_fn in (("hitting", _hitting_row), ("pitching", _pitching_row)):
        for split in _fetch_group(season, group):
            full_name = (split.get("player") or {}).get("fullName")
            if not full_name:
                continue
            key = normalize_name(full_name)
            merged.setdefault(key, {}).update(row_fn(split))
    return merged
