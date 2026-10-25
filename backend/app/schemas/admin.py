from pydantic import BaseModel


class RawDebugResponse(BaseModel):
    page: str
    status: str
    html_snippet: str | None = None
    error: str | None = None


class LoginDebugResponse(BaseModel):
    status_code: int
    final_url: str
    token_found: bool
    cookie_names: list[str]
    response_length: int
    html_snippet: str
