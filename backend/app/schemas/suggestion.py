from pydantic import BaseModel


class SuggestionRead(BaseModel):
    """One pickup suggestion. 'upgrade' compares a specific roster player
    against a specific available one at the same position; 'stash' is a
    speculative prospect add with no drop implied (bench/IL stash)."""

    kind: str  # "upgrade" | "stash"
    position: str | None = None
    add_full_name: str
    add_detail: str
    drop_full_name: str | None = None
    drop_detail: str | None = None
    reason: str


class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionRead]
    warnings: list[str]
