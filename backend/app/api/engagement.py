from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DbSession
from app.models.engagement import Bookmark, Comment, Follow, Like
from app.models.blog import Post

router = APIRouter(tags=["engagement"])

def post_or_404(post_id: int, db: DbSession) -> Post:
    post = db.get(Post, post_id)
    if post is None: raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.post("/posts/{post_id}/likes", status_code=status.HTTP_201_CREATED)
def like(post_id: int, current_user: CurrentUser, db: DbSession):
    post_or_404(post_id, db)
    if not db.get(Like, {"user_id": current_user.id, "post_id": post_id}): db.add(Like(user_id=current_user.id, post_id=post_id)); db.commit()
    return {"liked": True}

@router.delete("/posts/{post_id}/likes")
def unlike(post_id: int, current_user: CurrentUser, db: DbSession):
    item = db.get(Like, {"user_id": current_user.id, "post_id": post_id})
    if item: db.delete(item); db.commit()
    return {"liked": False}

@router.post("/posts/{post_id}/bookmarks", status_code=status.HTTP_201_CREATED)
def bookmark(post_id: int, current_user: CurrentUser, db: DbSession):
    post_or_404(post_id, db)
    if not db.get(Bookmark, {"user_id": current_user.id, "post_id": post_id}): db.add(Bookmark(user_id=current_user.id, post_id=post_id)); db.commit()
    return {"bookmarked": True}

@router.get("/bookmarks")
def bookmarks(current_user: CurrentUser, db: DbSession):
    return list(db.scalars(select(Post).join(Bookmark, Bookmark.post_id == Post.id).where(Bookmark.user_id == current_user.id)))

@router.post("/users/{user_id}/follow")
def follow(user_id: int, current_user: CurrentUser, db: DbSession):
    if user_id == current_user.id: raise HTTPException(status_code=400, detail="Cannot follow yourself")
    if not db.get(Follow, {"follower_id": current_user.id, "following_id": user_id}): db.add(Follow(follower_id=current_user.id, following_id=user_id)); db.commit()
    return {"following": True}

@router.post("/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
def comment(post_id: int, payload: dict, current_user: CurrentUser, db: DbSession):
    post_or_404(post_id, db); text = str(payload.get("comment", "")).strip()
    if not text: raise HTTPException(status_code=422, detail="Comment is required")
    item = Comment(post_id=post_id, user_id=current_user.id, parent_comment_id=payload.get("parent_comment_id"), comment=text); db.add(item); db.commit(); db.refresh(item)
    return {"id": item.id, "comment": item.comment}

@router.get("/posts/{post_id}/comments")
def comments(post_id: int, db: DbSession):
    post_or_404(post_id, db); return list(db.scalars(select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at)))
