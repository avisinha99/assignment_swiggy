from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict

from fastapi import WebSocket


class RealtimeHub:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._project_sockets: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, project_id: uuid.UUID, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._project_sockets[project_id].add(ws)

    async def disconnect(self, project_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            self._project_sockets[project_id].discard(ws)
            if not self._project_sockets[project_id]:
                self._project_sockets.pop(project_id, None)

    async def broadcast(self, project_id: uuid.UUID, message: dict) -> None:
        payload = json.dumps(message, separators=(",", ":"))
        async with self._lock:
            sockets = list(self._project_sockets.get(project_id, set()))
        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception:
                # best-effort cleanup happens on next disconnect
                pass


hub = RealtimeHub()
