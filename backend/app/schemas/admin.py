from pydantic import BaseModel


class RawDebugResponse(BaseModel):
    page: str
    status: str
    html_snippet: str | None = None
    total_length: int | None = None
    offset: int = 0
    error: str | None = None
