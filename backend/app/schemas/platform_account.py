import uuid

from pydantic import BaseModel


class LinkCBSAccountRequest(BaseModel):
    """CBS has no login API a server can POST credentials to anymore (its
    site is a modern logged-in-client-side Next.js app -- confirmed live,
    see integrations/cbs/client.py's login_debug). Connecting instead
    means: log into CBS normally in your own browser, then copy the
    resulting session cookie out of dev tools. auth_session is the one
    confirmed to matter; the others are optional extras to try if
    auth_session alone isn't enough to authenticate scraped page fetches."""

    league_name: str
    auth_session: str
    auth_state: str | None = None
    aws_alb: str | None = None
    aws_alb_cors: str | None = None


class PlatformAccountRead(BaseModel):
    id: uuid.UUID
    platform: str
    display_name: str | None = None
    is_connected: bool
