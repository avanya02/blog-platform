from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.blog import PostStatus


class PostCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=1)
    cover_image: str | None = Field(default=None, max_length=500)
    status: PostStatus = PostStatus.DRAFT


class PostUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    cover_image: str | None = Field(default=None, max_length=500)
    status: PostStatus | None = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    slug: str
    content: str
    cover_image: str | None
    status: PostStatus
    reading_time: int
    views: int
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
