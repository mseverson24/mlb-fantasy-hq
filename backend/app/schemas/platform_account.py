import uuid

from pydantic import BaseModel, field_validator


class ConnectCBSRequest(BaseModel):
    """CBS blocks plain server-to-server requests regardless of cookies
    (confirmed live: identical login-page responses across many different
    cookie combinations, even ones copied fresh from an authenticated
    session -- this is anti-scraping protection against the backend's own
    requests, not a credential problem). Connecting now just registers the
    league name and hands back a bookmarklet: a small button the user
    drags to their bookmarks bar and clicks while on their real,
    already-logged-in CBS pages, which posts the genuinely-rendered page
    HTML back to /cbs/ingest. No password or cookie ever touches this
    app's server."""

    league_name: str

    @field_validator("league_name")
    @classmethod
    def _normalize_league_name(cls, v: str) -> str:
        # Accept a pasted URL or host like "oldorchard.baseball.cbssports.com"
        # and keep just "oldorchard".
        v = v.strip().lower()
        v = v.removeprefix("https://").removeprefix("http://").split("/")[0]
        v = v.removesuffix(".cbssports.com").removesuffix(".baseball")
        if not v:
            raise ValueError("League name is required")
        return v


class ConnectCBSResponse(BaseModel):
    league_name: str
    ingest_token: str


class CBSIngestRequest(BaseModel):
    """Posted by the bookmarklet, authenticated by the opaque ingest_token
    rather than this app's normal JWT -- a JWT expires in 30 minutes,
    too short-lived for a bookmark the user might click again weeks
    later."""

    token: str
    page: str
    html: str


class CBSIngestResponse(BaseModel):
    page: str
    ok: bool
    message: str


class PlatformAccountRead(BaseModel):
    id: uuid.UUID
    platform: str
    display_name: str | None = None
    is_connected: bool
