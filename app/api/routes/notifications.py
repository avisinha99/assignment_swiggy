from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationOut, NotificationPage

router = APIRouter()


@router.get("/notifications", response_model=NotificationPage)
async def list_notifications(
    user: User = Depends(get_current_user),
    user_email: str | None = Query(default=None, description="View notifications for email"),
    cursor: int | None = Query(default=None, description="Return items with id < cursor"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> NotificationPage:
    target_user = user
    if user_email:
        target_user = await db.scalar(select(User).where(User.email == user_email.strip().lower()))
        if not target_user:
            return NotificationPage(items=[], next_cursor=None)

    q = select(Notification).where(Notification.user_id == target_user.id)
    if cursor is not None:
        q = q.where(Notification.id < cursor)
    q = q.order_by(Notification.id.desc()).limit(limit + 1)

    rows = (await db.scalars(q)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].id if has_more and rows else None
    return NotificationPage(
        items=[NotificationOut.model_validate(r, from_attributes=True) for r in rows],
        next_cursor=next_cursor,
    )

