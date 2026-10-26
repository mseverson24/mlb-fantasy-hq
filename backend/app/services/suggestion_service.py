"""Turns whatever's already synced (my roster + the CBS player pool) plus
two live, best-effort data pulls (MLB Stats API season lines, MLB Pipeline
prospect ranks) into concrete "drop X for Y" / "stash Z" suggestions.

Scoring is a deliberately simple heuristic, not a projection system: OPS for
hitters, a strikeouts-minus-ERA/WHIP composite for pitchers. Good enough to
rank "clearly better" from "clearly worse"; not meant to settle close calls.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.integrations import mlb_stats_api
from app.models import League, Player, PlayerStat, Roster, Team
from app.schemas.suggestion import SuggestionRead, SuggestionsResponse
from app.scrapers import mlb_pipeline_prospects

_PITCHER_POSITIONS = {"SP", "RP", "P"}
_MAX_UPGRADES = 10
_MAX_STASHES = 5


@dataclass
class _Scored:
    player: Player
    stat: PlayerStat | None
    score: float | None
    detail: str


def _is_pitcher(position: str | None) -> bool:
    return (position or "").upper() in _PITCHER_POSITIONS


def _score_player(player: Player, stat: PlayerStat | None) -> _Scored:
    if stat is None:
        return _Scored(player, None, None, "no stats synced")
    if _is_pitcher(player.position):
        if stat.era is None or stat.whip is None or stat.strikeouts is None:
            return _Scored(player, stat, None, "incomplete pitching line")
        score = stat.strikeouts - stat.era * 10 - stat.whip * 20
        return _Scored(player, stat, score, f"{stat.era:.2f} ERA, {stat.whip:.2f} WHIP, {stat.strikeouts} K")
    if stat.ops is None:
        return _Scored(player, stat, None, "incomplete hitting line")
    return _Scored(player, stat, stat.ops, f"{stat.ops:.3f} OPS")


def _refresh_player_stats(db: Session, season: str, warnings: list[str]) -> None:
    known_players = db.query(Player).filter(Player.cbs_player_id.isnot(None)).all()
    if not known_players:
        return
    try:
        stats_by_name = mlb_stats_api.fetch_season_stats_by_name(season)
    except Exception as exc:
        warnings.append(f"Could not refresh live MLB stats right now ({exc}); using whatever was last synced.")
        return

    for player in known_players:
        row = stats_by_name.get(mlb_stats_api.normalize_name(player.full_name))
        if row is None:
            continue
        stat = db.query(PlayerStat).filter(PlayerStat.player_id == player.id, PlayerStat.season == season).first()
        if stat is None:
            stat = PlayerStat(player_id=player.id, season=season)
            db.add(stat)
        for field, value in row.items():
            setattr(stat, field, value)
    db.commit()


def _latest_stat(db: Session, player_id, season: str) -> PlayerStat | None:
    return db.query(PlayerStat).filter(PlayerStat.player_id == player_id, PlayerStat.season == season).first()


def build_suggestions(db: Session, league: League) -> SuggestionsResponse:
    warnings: list[str] = []
    _refresh_player_stats(db, league.season, warnings)

    my_team = db.query(Team).filter(Team.league_id == league.id, Team.is_my_team.is_(True)).first()
    if my_team is None:
        return SuggestionsResponse(suggestions=[], warnings=["No roster synced yet -- click the bookmarklet on your My Team page first."])

    roster = db.query(Roster).filter(Roster.team_id == my_team.id, Roster.week.is_(None)).first()
    roster_players = roster.roster_players if roster else []
    my_player_ids = {rp.player_id for rp in roster_players}

    mine_by_position: dict[str, list[_Scored]] = {}
    for rp in roster_players:
        player = rp.player
        position = player.position or "UNK"
        stat = _latest_stat(db, player.id, league.season)
        mine_by_position.setdefault(position, []).append(_score_player(player, stat))

    pool = db.query(Player).filter(Player.cbs_player_id.isnot(None), ~Player.id.in_(my_player_ids)).all() if my_player_ids else db.query(Player).filter(Player.cbs_player_id.isnot(None)).all()
    if not pool:
        warnings.append(
            "No available players synced yet -- click the bookmarklet on CBS's Players page (filtered to Free "
            "Agents) to see upgrade suggestions."
        )

    pool_by_position: dict[str, list[_Scored]] = {}
    for player in pool:
        position = player.position or "UNK"
        stat = _latest_stat(db, player.id, league.season)
        scored = _score_player(player, stat)
        if scored.score is not None:
            pool_by_position.setdefault(position, []).append(scored)

    upgrades: list[tuple[float, SuggestionRead]] = []
    for position, candidates in pool_by_position.items():
        mine = mine_by_position.get(position, [])
        if not mine:
            continue
        best_candidate = max(candidates, key=lambda c: c.score)
        weakest_mine = min(mine, key=lambda s: s.score if s.score is not None else float("-inf"))
        if weakest_mine.score is not None and best_candidate.score <= weakest_mine.score:
            continue
        gap = best_candidate.score - (weakest_mine.score if weakest_mine.score is not None else 0.0)
        upgrades.append(
            (
                gap,
                SuggestionRead(
                    kind="upgrade",
                    position=position,
                    add_full_name=best_candidate.player.full_name,
                    add_detail=best_candidate.detail,
                    drop_full_name=weakest_mine.player.full_name,
                    drop_detail=weakest_mine.detail,
                    reason=(
                        f"{best_candidate.player.full_name} ({best_candidate.detail}) is available and outproducing "
                        f"your {position} {weakest_mine.player.full_name} ({weakest_mine.detail})."
                    ),
                ),
            )
        )
    upgrades.sort(key=lambda pair: pair[0], reverse=True)
    suggestions = [s for _, s in upgrades[:_MAX_UPGRADES]]

    known_names = {mlb_stats_api.normalize_name(p.full_name) for p in db.query(Player.full_name).all()}
    try:
        prospects = mlb_pipeline_prospects.fetch_top_prospects(limit=100)
    except Exception as exc:
        warnings.append(f"Could not load MLB Pipeline prospects right now ({exc}).")
        prospects = []

    my_positions = set(mine_by_position.keys())
    stash_count = 0
    for prospect in prospects:
        if stash_count >= _MAX_STASHES:
            break
        if mlb_stats_api.normalize_name(prospect.full_name) in known_names:
            continue
        if prospect.position and my_positions and not any(
            prospect.position.upper() in pos.upper() or pos.upper() in prospect.position.upper() for pos in my_positions
        ):
            continue
        suggestions.append(
            SuggestionRead(
                kind="stash",
                position=prospect.position,
                add_full_name=prospect.full_name,
                add_detail=f"#{prospect.rank} prospect" + (f" ({prospect.level})" if prospect.level else ""),
                drop_full_name=None,
                drop_detail=None,
                reason=(
                    f"{prospect.full_name} is MLB Pipeline's #{prospect.rank} overall prospect"
                    + (f", currently at {prospect.level}" if prospect.level else "")
                    + " and isn't on CBS's player list yet -- worth a speculative stash before he debuts."
                ),
            )
        )
        stash_count += 1

    return SuggestionsResponse(suggestions=suggestions, warnings=warnings)
