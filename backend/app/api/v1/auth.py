from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, MeResponse, RefreshRequest, RegisterRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user = auth_service.register_user(db, payload.email, payload.password, payload.display_name)
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    access_token, refresh_token = auth_service.issue_tokens(db, user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user = auth_service.authenticate_user(db, payload.email, payload.password)
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    access_token, refresh_token = auth_service.issue_tokens(db, user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        access_token, refresh_token = auth_service.rotate_refresh_token(db, payload.refresh_token)
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/bootstrap-admin", response_model=MeResponse)
def bootstrap_admin(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> User:
    """One-time self-promotion: makes the calling user an admin, but only
    if no admin exists yet anywhere in the system. Exists because this app
    has no admin UI to manage that flag another way yet, and there's no
    direct database access to flip it by hand in production. Safe as a
    standing endpoint even after use -- once any admin exists, every call
    here (including a compromised/curious non-admin user) 403s."""
    if db.query(User).filter(User.is_admin.is_(True)).first() is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="An admin already exists")
    current_user.is_admin = True
    db.commit()
    db.refresh(current_user)
    return current_user
