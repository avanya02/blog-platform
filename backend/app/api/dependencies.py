from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer()
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)], db: DbSession) -> User:
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise credentials_error from exc
    user = db.get(User, user_id)
    if user is None or user.is_banned:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access is required")
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
