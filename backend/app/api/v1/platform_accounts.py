import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Platform, PlatformAccount, User
from app.schemas.admin import RawDebugResponse
from app.schemas.platform_account import (
    CBSIngestRequest,
    CBSIngestResponse,
    ConnectCBSRequest,
    ConnectCBSResponse,
    PlatformAccountRead,
)
from app.services import league_sync_service

router = APIRouter(prefix="/platform-accounts", tags=["platform-accounts"])

_CURRENT_SEASON = "2026"
_DEBUG_WINDOW = 15000


@router.get("", response_model=list[PlatformAccountRead])
def list_platform_accounts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[PlatformAccountRead]:
    accounts = db.query(PlatformAccount).filter(PlatformAccount.user_id == current_user.id).all()
    return [
        PlatformAccountRead(
            id=a.id, platform=a.platform.value, display_name=a.display_name, is_connected=bool(a.ingest_token)
        )
        for a in accounts
    ]


@router.post("/cbs", response_model=ConnectCBSResponse, status_code=status.HTTP_201_CREATED)
def connect_cbs_account(
    payload: ConnectCBSRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConnectCBSResponse:
    """Registers the league name and issues a long-lived ingest token for
    the bookmarklet -- see schemas/platform_account.py's ConnectCBSRequest
    docstring for why plain server-side CBS requests don't work at all."""
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
            extra_data={},
        )
        db.add(account)
    account.display_name = payload.league_name
    if not account.ingest_token:
        account.ingest_token = secrets.token_urlsafe(32)
    account.extra_data = {**(account.extra_data or {}), "league_name": payload.league_name}
    db.commit()
    db.refresh(account)

    return ConnectCBSResponse(league_name=payload.league_name, ingest_token=account.ingest_token)


@router.post("/cbs/ingest", response_model=CBSIngestResponse)
def ingest_cbs_page(payload: CBSIngestRequest, db: Session = Depends(get_db)) -> CBSIngestResponse:
    """Called cross-origin from the bookmarklet running on a cbssports.com
    page -- authenticated by the opaque per-account token, not a JWT (see
    CBSIngestRequest's docstring). No user session/cookie required."""
    account = (
        db.query(PlatformAccount)
        .filter(PlatformAccount.platform == Platform.cbs, PlatformAccount.ingest_token == payload.token)
        .first()
    )
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown or revoked ingest token")

    try:
        message = league_sync_service.ingest_page(
            db, account.user_id, account, _CURRENT_SEASON, payload.page, payload.html
        )
        return CBSIngestResponse(page=payload.page, ok=True, message=message)
    except ValueError as exc:
        return CBSIngestResponse(page=payload.page, ok=False, message=str(exc))
    except Exception as exc:
        return CBSIngestResponse(page=payload.page, ok=False, message=f"{type(exc).__name__}: {exc}")


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_platform_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a connected account (and its league links, via cascade).
    Only the owner can delete their own account."""
    account = (
        db.query(PlatformAccount)
        .filter(PlatformAccount.id == account_id, PlatformAccount.user_id == current_user.id)
        .first()
    )
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    db.delete(account)
    db.commit()


@router.get("/cbs/raw-debug", response_model=RawDebugResponse)
def cbs_raw_debug(
    page: str = "roster",
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RawDebugResponse:
    """Serves back whatever the bookmarklet last ingested for this page
    type (see RawDebugResponse's docstring) -- lets the real markup be
    inspected and the mapper selectors corrected against it."""
    account = (
        db.query(PlatformAccount)
        .filter(PlatformAccount.user_id == current_user.id, PlatformAccount.platform == Platform.cbs)
        .order_by(PlatformAccount.updated_at.desc())
        .first()
    )
    if account is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No connected CBS account")

    entry = (account.extra_data.get("ingested") or {}).get(page)
    if entry is None:
        return RawDebugResponse(page=page, status="not_ingested", error="No page ingested yet -- use the bookmarklet first")

    html = entry.get("html", "")
    return RawDebugResponse(
        page=page,
        status="ok",
        html_snippet=html[offset : offset + _DEBUG_WINDOW],
        total_length=entry.get("total_length", len(html)),
        offset=offset,
        ingested_at=entry.get("at"),
    )
