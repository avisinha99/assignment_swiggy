from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.realtime.hub import hub


async def log_activity(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    actor_id: uuid.UUID,
    event_type: str,
    issue_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    a = Activity(
        project_id=project_id,
        issue_id=issue_id,
        actor_id=actor_id,
        event_type=event_type,
        payload=json.dumps(payload or {}, separators=(",", ":")),
    )
    db.add(a)
    # Best-effort realtime broadcast (activity_id might not be assigned yet).
    try:
        await hub.broadcast(
            project_id,
            {"type": event_type, "project_id": str(project_id), "issue_id": str(issue_id) if issue_id else None, "payload": payload or {}},
        )
    except Exception:
        pass
