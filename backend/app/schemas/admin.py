from pydantic import BaseModel


class RawDebugResponse(BaseModel):
    page: str
    status: str
    html_snippet: str | None = None
    error: str | None = None
