from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, leagues, platform_accounts, rankings
from app.config import settings

app = FastAPI(title="MLB FantasyHQ")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # The CBS bookmarklet runs *on* a cbssports.com page and POSTs to
    # /platform-accounts/cbs/ingest from there -- that call is authenticated
    # by its own opaque per-account token (see that endpoint), not cookies,
    # so allowing this origin doesn't expose anything else.
    allow_origin_regex=r"https://([a-z0-9-]+\.)*cbssports\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(platform_accounts.router, prefix="/api/v1")
app.include_router(leagues.router, prefix="/api/v1")
app.include_router(rankings.router, prefix="/api/v1")


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok"}
