from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserRole


class PublicUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    bio: str | None
    profile_picture: str | None
    created_at: datetime


class ProfileResponse(PublicUser):
    email: str
    role: UserRole


class ProfileUpdateRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    bio: str | None = Field(default=None, max_length=500)
    profile_picture: str | None = Field(default=None, max_length=500)
