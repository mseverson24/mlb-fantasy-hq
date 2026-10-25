import uuid

from pydantic import BaseModel


class LinkCBSAccountRequest(BaseModel):
    username: str
    password: str
    league_name: str


class PlatformAccountRead(BaseModel):
    id: uuid.UUID
    platform: str
    display_name: str | None = None
    is_connected: bool
