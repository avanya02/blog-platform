from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DbSession
from app.models.user import User
from app.schemas.user import ProfileResponse, ProfileUpdateRequest, PublicUser

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/profile", response_model=ProfileResponse)
def profile(current_user: CurrentUser) -> User: return current_user

@router.put("/profile", response_model=ProfileResponse)
def update_profile(payload: ProfileUpdateRequest, current_user: CurrentUser, db: DbSession) -> User:
    values = payload.model_dump(exclude_unset=True)
    if "username" in values and values["username"] != current_user.username and db.scalar(select(User).where(User.username == values["username"])):
        raise HTTPException(status_code=409, detail="Username is already taken")
    for field, value in values.items(): setattr(current_user, field, value)
    db.commit(); db.refresh(current_user)
    return current_user

@router.get("/{user_id}", response_model=PublicUser)
def public_profile(user_id: int, db: DbSession) -> User:
    user = db.get(User, user_id)
    if user is None: raise HTTPException(status_code=404, detail="User not found")
    return user
