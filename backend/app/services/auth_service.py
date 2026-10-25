from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models import RefreshToken, User


class AuthError(Exception):
    pass


def register_user(db: Session, email: str, password: str, display_name: str) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise AuthError("Email already registered")
    user = User(email=email, hashed_password=hash_password(password), display_name=display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise AuthError("Invalid email or password")
    return user


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(subject=str(user.id))
    raw_refresh_token = generate_refresh_token()
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(refresh_token)
    # Covers register, login, and silent refresh-token rotation -- see the
    # sibling NFL app's User.last_active_at for why refresh counts too
    # (access tokens expire every 30 minutes and get silently renewed in
    # the background, so a login-only timestamp reads stale for an
    # actively-returning user).
    user.last_active_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    return access_token, raw_refresh_token


def rotate_refresh_token(db: Session, raw_refresh_token: str) -> tuple[str, str]:
    token_hash = hash_refresh_token(raw_refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if not stored or stored.revoked_at is not None or stored.expires_at < datetime.now(timezone.utc):
        raise AuthError("Invalid or expired refresh token")
    stored.revoked_at = datetime.now(timezone.utc)
    user = db.query(User).filter(User.id == stored.user_id).first()
    if not user:
        raise AuthError("User not found")
    db.commit()
    return issue_tokens(db, user)
