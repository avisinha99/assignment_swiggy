from __future__ import annotations

import json
import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.user import User


# Match @email (basic, good enough for demo)
MENTION_RE = re.compile(r"@([A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+)")


def extract_mentions(text: str) -> list[str]:
    return list(dict.fromkeys(m.group(1).lower() for m in MENTION_RE.finditer(text or "")))


async def notify(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    type: str,
    payload: dict[str, Any],
) -> None:
    db.add(Notification(user_id=user_id, type=type, payload=json.dumps(payload, separators=(",", ":"))))


async def notify_mentions(
    db: AsyncSession,
    *,
    body: str,
    payload: dict[str, Any],
) -> int:
    emails = extract_mentions(body)
    if not emails:
        return 0
    users = (
        await db.scalars(select(User).where(User.email.in_(emails), User.is_active == True))  # noqa: E712
    ).all()
    for u in users:
        await notify(db, user_id=u.id, type="mention", payload=payload)
    return len(users)
