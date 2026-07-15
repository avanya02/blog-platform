import re

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.api.dependencies import AdminUser, DbSession
from app.models.blog import Category, Post
from app.models.engagement import Comment, Like
from app.models.user import User
from app.schemas.discovery import CategoryResponse

router = APIRouter(prefix="/admin", tags=["admin"])

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

@router.get("/analytics")
def analytics(_: AdminUser, db: DbSession):
    return {"users": db.scalar(select(func.count()).select_from(User)) or 0, "posts": db.scalar(select(func.count()).select_from(Post)) or 0, "comments": db.scalar(select(func.count()).select_from(Comment)) or 0, "likes": db.scalar(select(func.count()).select_from(Like)) or 0, "views": db.scalar(select(func.coalesce(func.sum(Post.views), 0))) or 0}

@router.put("/users/{user_id}/ban")
def ban_user(user_id: int, _: AdminUser, db: DbSession):
    user = db.get(User, user_id)
    if user is None: raise HTTPException(status_code=404, detail="User not found")
    user.is_banned = True; db.commit()
    return {"banned": True}

@router.delete("/posts/{post_id}")
def remove_post(post_id: int, _: AdminUser, db: DbSession):
    post = db.get(Post, post_id)
    if post is None: raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post); db.commit()

@router.get("/categories", response_model=list[CategoryResponse])
def categories(_: AdminUser, db: DbSession): return list(db.scalars(select(Category).order_by(Category.name)))

@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(payload: dict, _: AdminUser, db: DbSession):
    name = str(payload.get("name", "")).strip(); slug = slugify(name)
    if not name or not slug: raise HTTPException(status_code=422, detail="A category name is required")
    if db.scalar(select(Category).where(Category.slug == slug)): raise HTTPException(status_code=409, detail="Category already exists")
    category = Category(name=name, slug=slug); db.add(category); db.commit(); db.refresh(category); return category

@router.delete("/categories/{category_id}")
def delete_category(category_id: int, _: AdminUser, db: DbSession):
    category = db.get(Category, category_id)
    if category is None: raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category); db.commit()
