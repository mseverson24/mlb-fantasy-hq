from pydantic import BaseModel


class RawDebugResponse(BaseModel):
    page: str
    status: str
    html_snippet: str | None = None
    total_length: int | None = None
    offset: int = 0
    error: str | None = None
    status_code: int | None = None
    final_url: str | None = None
    redirect_chain: list[str] = []
    set_cookie_names: list[str] = []
