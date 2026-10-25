from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models import User
from app.scrapers import cbs_baseball_rankings
from app.schemas.player import RankedPlayerRead

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("", response_model=list[RankedPlayerRead])
def get_rankings(_current_user: User = Depends(get_current_user)) -> list[RankedPlayerRead]:
    """Public CBS fantasy baseball rankings -- no CBS login needed, unlike
    the league/roster endpoints. See cbs_baseball_rankings.py's docstring
    for the "best effort, unverified" caveat on its selectors."""
    try:
        rows = cbs_baseball_rankings.fetch_rankings()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Could not load rankings: {exc}") from exc
    return [RankedPlayerRead(rank=r.rank, full_name=r.full_name, position=r.position) for r in rows]
