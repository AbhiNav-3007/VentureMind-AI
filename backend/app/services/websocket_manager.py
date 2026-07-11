"""
VentureMind AI — WebSocket Connection Manager
Handles live progress broadcasting from agent workflow to the frontend.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

from app.core.logging import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """
    Manages per-startup WebSocket connections for live agent progress updates.
    Multiple clients can subscribe to the same startup_id.
    """

    def __init__(self) -> None:
        # startup_id → list of connected WebSocket clients
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, startup_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[startup_id].append(websocket)
        logger.info("WebSocket connected", startup_id=startup_id)

    def disconnect(self, startup_id: str, websocket: WebSocket) -> None:
        try:
            self._connections[startup_id].remove(websocket)
        except ValueError:
            pass
        logger.info("WebSocket disconnected", startup_id=startup_id)

    async def broadcast(self, startup_id: str, message: dict[str, Any]) -> None:
        """Send a JSON message to all clients watching this startup."""
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(startup_id, [])):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        # Clean up closed connections
        for ws in dead:
            self.disconnect(startup_id, ws)


# Singleton
ws_manager = WebSocketManager()
