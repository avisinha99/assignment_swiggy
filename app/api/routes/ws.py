from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.activity import Activity
from app.models.project_member import ProjectMember
from app.models.user import User
from app.realtime.hub import hub

router = APIRouter()


async def _get_user_from_ws_token(db: AsyncSession, token: str) -> User | None:
    # No-auth mode: ignore token and use first active user.
    return await db.scalar(select(User).where(User.is_active == True).order_by(User.created_at.asc()))  # noqa: E712


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    project_id: uuid.UUID = Query(...),
    token: str = Query(default="demo"),
    since_activity_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> None:
    user = await _get_user_from_ws_token(db, token)
    if not user:
        await ws.close(code=4401)
        return

    member = await db.scalar(
        select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user.id)
    )
    if not member:
        await ws.close(code=4403)
        return

    await hub.connect(project_id, ws)
    try:
        # replay missed events using activity log
        if since_activity_id is not None:
            rows = (
                await db.scalars(
                    select(Activity)
                    .where(Activity.project_id == project_id, Activity.id > since_activity_id)
                    .order_by(Activity.id.asc())
                    .limit(500)
                )
            ).all()
            for a in rows:
                await ws.send_json(
                    {
                        "type": a.event_type,
                        "activity_id": a.id,
                        "project_id": str(a.project_id),
                        "issue_id": str(a.issue_id) if a.issue_id else None,
                        "payload": a.payload,
                        "created_at": a.created_at.isoformat(),
                    }
                )

        await hub.broadcast(project_id, {"type": "presence_join", "user_id": str(user.id)})

        while True:
            # keep connection alive; ignore client messages for now
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await hub.disconnect(project_id, ws)
        await hub.broadcast(project_id, {"type": "presence_leave", "user_id": str(user.id)})

