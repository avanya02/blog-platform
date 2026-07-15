from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DbSession
from app.models.blog import Post, PostStatus
from app.models.engagement import Like

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/analytics")
def analytics(current_user: CurrentUser, db: DbSession):
    posts = list(db.scalars(select(Post).where(Post.user_id == current_user.id)))
    post_ids = [post.id for post in posts]
    likes = 0 if not post_ids else db.scalar(select(func.count()).select_from(Like).where(Like.post_id.in_(post_ids))) or 0
    return {"posts": len(posts), "published": sum(post.status == PostStatus.PUBLISHED for post in posts), "drafts": sum(post.status == PostStatus.DRAFT for post in posts), "views": sum(post.views for post in posts), "likes": likes}
