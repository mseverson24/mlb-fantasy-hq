from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.integrations.cbs.adapter import CBSAdapter
from app.models import Platform, PlatformAccount, User
from app.schemas.admin import RawDebugResponse
from app.schemas.league import LeagueRead
from app.schemas.platform_account import LinkCBSAccountRequest, PlatformAccountRead
from app.services import league_sync_service

router = APIRouter(prefix="/platform-accounts", tags=["platform-accounts"])

_CURRENT_SEASON = "2026"


@router.get("", response_model=list[PlatformAccountRead])
def list_platform_accounts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[PlatformAccountRead]:
    accounts = db.query(PlatformAccount).filter(PlatformAccount.user_id == current_user.id).all()
    return [
        PlatformAccountRead(
            id=a.id, platform=a.platform.value, display_name=a.display_name, is_connected=bool(a.access_token)
        )
        for a in accounts
    ]


@router.post("/cbs", response_model=LeagueRead, status_code=status.HTTP_201_CREATED)
def link_cbs_account(
    payload: LinkCBSAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeagueRead:
    """CBS has no login endpoint a server can authenticate against anymore
    (confirmed live -- its site is a client-side-rendered app now, see
    integrations/cbs/client.py's history). Connecting instead means: the
    user logs into CBS normally in their own browser, then pastes the
    resulting auth_session cookie here -- no password ever touches this
    app. Stores the cookie(s) and immediately syncs the league/roster so
    the connection is proven working (or fails loudly here) rather than
    silently deferred to the first page load."""
    cookies = {"auth_session": payload.auth_session}
    if payload.auth_state:
        cookies["auth_state"] = payload.auth_state
    if payload.aws_alb:
        cookies["AWSALB"] = payload.aws_alb
    if payload.aws_alb_cors:
        cookies["AWSALBCORS"] = payload.aws_alb_cors

    account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.user_id == current_user.id,
            PlatformAccount.platform == Platform.cbs,
            PlatformAccount.external_user_id == payload.league_name,
        )
        .first()
    )
    if account is None:
        account = PlatformAccount(
            user_id=current_user.id,
            platform=Platform.cbs,
            external_user_id=payload.league_name,
        )
        db.add(account)
    account.display_name = payload.league_name
    account.access_token = payload.auth_session
    account.extra_data = {"cookies": cookies, "league_name": payload.league_name}
    db.commit()
    db.refresh(account)

    try:
        league = league_sync_service.sync_league(db, current_user.id, account, _CURRENT_SEASON)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Saved the cookie, but couldn't read your league/roster yet: {exc}",
        ) from exc

    return LeagueRead(
        id=league.id,
        name=league.name,
        season=league.season,
        scoring_type=league.scoring_type,
        num_teams=league.num_teams,
        roster_positions=league.roster_positions,
        last_synced_at=league.last_synced_at,
    )


@router.get("/cbs/raw-debug", response_model=RawDebugResponse)
def cbs_raw_debug(
    page: str = "roster",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RawDebugResponse:
    """Temporary diagnostic, not a permanent feature: CBS's logged-in page
    structure was unverified when this adapter was built (no real account
    to test against). Returns a snippet of the actual fetched HTML for
    whichever page (roster/standings/league/players) so the real selectors
    in integrations/cbs/mapper.py can be corrected against real data,
    rather than guessed at a second time. Safe to delete once CBS sync is
    confirmed working end to end."""
    account = (
        db.query(PlatformAccount)
        .filter(PlatformAccount.user_id == current_user.id, PlatformAccount.platform == Platform.cbs)
        .first()
    )
    if account is None or not account.access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No connected CBS account")

    league_name = account.extra_data.get("league_name")
    cookies = account.extra_data.get("cookies", {})
    adapter = CBSAdapter(league_name=league_name, season=_CURRENT_SEASON, cookies=cookies)

    fetchers = {
        "league": adapter.client.get_league_home_html,
        "roster": lambda: adapter.client.get_roster_html(team_id=None),
        "standings": adapter.client.get_standings_html,
        "players": adapter.client.get_players_html,
    }
    fetcher = fetchers.get(page)
    if fetcher is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown page {page!r}")

    try:
        html = fetcher()
        return RawDebugResponse(page=page, status="ok", html_snippet=html[:8000])
    except Exception as exc:
        return RawDebugResponse(page=page, status="error", error=f"{type(exc).__name__}: {exc}")
