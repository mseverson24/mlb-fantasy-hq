from pydantic import BaseModel, Field

from app.schemas.user import UserRead


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    display_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeResponse(UserRead):
    pass
