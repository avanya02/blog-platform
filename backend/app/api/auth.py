import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, update

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import PasswordResetToken, User
from app.schemas.auth import ForgotPasswordRequest, LoginRequest, MessageResponse, RegisterRequest, ResetPasswordRequest, TokenResponse
from app.schemas.user import ProfileResponse

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> User:
    if db.scalar(select(User).where((User.email == str(payload.email).lower()) | (User.username == payload.username))):
        raise HTTPException(status_code=409, detail="Email or username is already registered")
    user = User(username=payload.username, email=str(payload.email).lower(), password_hash=hash_password(payload.password))
    db.add(user); db.commit(); db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="This account is unavailable")
    return TokenResponse(access_token=create_access_token(user.id, user.role.value))

@router.get("/me", response_model=ProfileResponse)
def me(current_user: CurrentUser) -> User:
    return current_user

@router.post("/logout", response_model=MessageResponse)
def logout(_: CurrentUser) -> MessageResponse:
    return MessageResponse(message="Signed out. Remove the access token from the client.")

@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: DbSession) -> MessageResponse:
    response = MessageResponse(message="If an account exists, reset instructions have been created.")
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None: return response
    now = datetime.now(timezone.utc)
    db.execute(update(PasswordResetToken).where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)).values(used_at=now))
    token = secrets.token_urlsafe(32)
    db.add(PasswordResetToken(user_id=user.id, token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=now + timedelta(minutes=30)))
    db.commit()
    if get_settings().environment == "development": response.development_reset_token = token
    return response

@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: DbSession) -> MessageResponse:
    record = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hashlib.sha256(payload.token.encode()).hexdigest()))
    now = datetime.now(timezone.utc)
    if record is None or record.used_at is not None or record.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=400, detail="The reset token is invalid or expired")
    user = db.get(User, record.user_id)
    if user is None: raise HTTPException(status_code=400, detail="The reset token is invalid")
    user.password_hash = hash_password(payload.new_password); record.used_at = now; db.commit()
    return MessageResponse(message="Password updated. You can now sign in.")
