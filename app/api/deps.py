from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User


async def get_current_user(
    db: AsyncSession = Depends(get_db),
) -> User:
    # No-auth mode: use first active user (seeded).
    user = await db.scalar(select(User).where(User.is_active == True).order_by(User.created_at.asc()))  # noqa: E712
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No active users found. Run scripts/seed.py first.",
        )
    return user
