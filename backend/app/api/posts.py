import re
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DbSession
from app.models.blog import Category, Post, PostStatus, Tag, post_tags
from app.schemas.post import PostCreateRequest, PostResponse, PostUpdateRequest

router = APIRouter(prefix="/posts", tags=["posts"])


def make_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "post"


def unique_slug(title: str, db: DbSession, exclude_id: int | None = None) -> str:
    base = make_slug(title); slug = base; number = 2
    while True:
        query = select(Post.id).where(Post.slug == slug)
        if exclude_id is not None: query = query.where(Post.id != exclude_id)
        if db.scalar(query) is None: return slug
        slug = f"{base}-{number}"; number += 1


def reading_time(content: str) -> int:
    return max(1, (len(content.split()) + 199) // 200)


def get_owned_post(post_id: int, current_user: CurrentUser, db: DbSession) -> Post:
    post = db.get(Post, post_id)
    if post is None: raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id: raise HTTPException(status_code=403, detail="You do not own this post")
    return post


@router.get("", response_model=list[PostResponse])
def list_posts(db: DbSession, page: int = Query(1, ge=1), page_size: int = Query(12, ge=1, le=50), category: str | None = None, tag: str | None = None) -> list[Post]:
    statement = select(Post).where(Post.status == PostStatus.PUBLISHED)
    if category: statement = statement.join(Category).where(Category.slug == category)
    if tag: statement = statement.join(post_tags).join(Tag).where(Tag.slug == tag)
    return list(db.scalars(statement.order_by(Post.published_at.desc()).offset((page - 1) * page_size).limit(page_size)))


@router.get("/mine", response_model=list[PostResponse])
def my_posts(current_user: CurrentUser, db: DbSession) -> list[Post]:
    return list(db.scalars(select(Post).where(Post.user_id == current_user.id).order_by(Post.updated_at.desc())))


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: DbSession) -> Post:
    post = db.get(Post, post_id)
    if post is None or post.status != PostStatus.PUBLISHED: raise HTTPException(status_code=404, detail="Post not found")
    post.views += 1; db.commit(); db.refresh(post)
    return post


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreateRequest, current_user: CurrentUser, db: DbSession) -> Post:
    post = Post(user_id=current_user.id, title=payload.title, slug=unique_slug(payload.title, db), content=payload.content, cover_image=payload.cover_image, status=payload.status, reading_time=reading_time(payload.content))
    if payload.status == PostStatus.PUBLISHED: post.published_at = datetime.now(timezone.utc)
    db.add(post); db.commit(); db.refresh(post)
    return post


@router.put("/{post_id}", response_model=PostResponse)
def update_post(post_id: int, payload: PostUpdateRequest, current_user: CurrentUser, db: DbSession) -> Post:
    post = get_owned_post(post_id, current_user, db); values = payload.model_dump(exclude_unset=True)
    if "title" in values: post.title = values["title"]; post.slug = unique_slug(values["title"], db, post.id)
    for field in ("content", "cover_image", "status"):
        if field in values: setattr(post, field, values[field])
    if "content" in values: post.reading_time = reading_time(values["content"])
    if post.status == PostStatus.PUBLISHED and post.published_at is None: post.published_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, current_user: CurrentUser, db: DbSession) -> None:
    db.delete(get_owned_post(post_id, current_user, db)); db.commit()
