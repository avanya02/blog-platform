from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.database.session import get_db
from app.models.blog import Category, Post, PostStatus, Tag, post_tags
from app.schemas.discovery import CategoryResponse, TagResponse
from app.schemas.post import PostResponse
from sqlalchemy.orm import Session
from fastapi import Depends

router = APIRouter(tags=["discovery"])


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)))


@router.get("/tags", response_model=list[TagResponse])
def list_tags(db: Session = Depends(get_db)) -> list[Tag]:
    return list(db.scalars(select(Tag).order_by(Tag.name)))


@router.get("/search", response_model=list[PostResponse])
def search_posts(
    db: Session = Depends(get_db), q: str = Query(min_length=1, max_length=100), category: str | None = None,
    tag: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(12, ge=1, le=50),
) -> list[Post]:
    statement = select(Post).where(Post.status == PostStatus.PUBLISHED, or_(Post.title.ilike(f"%{q}%"), Post.content.ilike(f"%{q}%")))
    if category:
        statement = statement.join(Category).where(Category.slug == category)
    if tag:
        statement = statement.join(post_tags).join(Tag).where(Tag.slug == tag)
    statement = statement.order_by(Post.published_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return list(db.scalars(statement))
