"""
VentureMind AI — WebSocket Route for Live Agent Progress
WS /api/v1/ws/{startup_id}
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.services.websocket_manager import ws_manager

logger = get_logger(__name__)
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{startup_id}")
async def agent_progress_ws(websocket: WebSocket, startup_id: str) -> None:
    """
    WebSocket endpoint that streams live agent execution progress to the frontend.

    The frontend connects immediately after submitting an idea.
    Messages are JSON: {event, startup_id, current_agent, progress, agent_statuses}
    """
    await ws_manager.connect(startup_id, websocket)
    try:
        # Keep connection alive until client disconnects
        while True:
            await websocket.receive_text()  # heartbeat / ping
    except WebSocketDisconnect:
        ws_manager.disconnect(startup_id, websocket)
        logger.info("WS client disconnected", startup_id=startup_id)
