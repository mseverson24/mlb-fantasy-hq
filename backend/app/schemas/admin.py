from pydantic import BaseModel


class RawDebugResponse(BaseModel):
    """Serves back whatever HTML the bookmarklet last ingested for this
    page type -- live server-side fetches to CBS are blocked (see
    integrations/cbs/client.py), so this is no longer a live fetch."""

    page: str
    status: str
    html_snippet: str | None = None
    total_length: int | None = None
    offset: int = 0
    error: str | None = None
    ingested_at: str | None = None
