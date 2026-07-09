"""
VentureMind AI — Agent Timeline API Route
GET /api/v1/startups/{startup_id}/timelines  — full agent reasoning timelines
GET /api/v1/startups/{startup_id}/validation — validation result
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import raise_not_found
from app.db.session import get_db
from app.models.agent_log import AgentLog
from app.models.blueprint import Blueprint
from app.models.startup import StartupIdea

router = APIRouter(prefix="/startups", tags=["Agent Timelines"])


@router.get("/{startup_id}/timelines")
async def get_agent_timelines(
    startup_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Return the full reasoning timelines for all agents of a completed workflow.
    Used by the Agent Reasoning Timeline panel on the frontend.
    """
    bp_result = await db.execute(
        select(Blueprint).where(Blueprint.startup_id == uuid.UUID(startup_id))
    )
    bp = bp_result.scalar_one_or_none()
    if not bp:
        raise_not_found("Blueprint")

    # Timelines are stored in final_recommendations JSON column
    timelines = {}
    if bp.final_recommendations and isinstance(bp.final_recommendations, dict):
        timelines = bp.final_recommendations.get("agent_timelines", {})

    # Also fetch from agent logs for current_task / tool info
    logs_result = await db.execute(
        select(AgentLog)
        .where(AgentLog.startup_id == uuid.UUID(startup_id))
        .order_by(AgentLog.created_at)
    )
    logs = logs_result.scalars().all()

    return {
        "startup_id": startup_id,
        "timelines": timelines,
        "agent_logs": [
            {
                "agent_name": log.agent_name,
                "agent_role": log.agent_role,
                "status": log.status,
                "current_task": log.current_task,
                "progress": log.progress,
                "execution_time_seconds": log.execution_time_seconds,
                "output_summary": log.output_summary,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "finished_at": log.finished_at.isoformat() if log.finished_at else None,
                "metadata": log.agent_metadata or {},
            }
            for log in logs
        ],
    }


@router.get("/{startup_id}/validation")
async def get_validation_result(
    startup_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return the Planner's validation result for a completed blueprint."""
    bp_result = await db.execute(
        select(Blueprint).where(Blueprint.startup_id == uuid.UUID(startup_id))
    )
    bp = bp_result.scalar_one_or_none()
    if not bp:
        raise_not_found("Blueprint")

    validation = {}
    if bp.final_recommendations and isinstance(bp.final_recommendations, dict):
        validation = bp.final_recommendations.get("validation", {})

    return {
        "startup_id": startup_id,
        "validation": validation,
        "feasibility_score": bp.final_recommendations.get("feasibility_score") if bp.final_recommendations else None,
        "urgency_level": bp.final_recommendations.get("urgency_level") if bp.final_recommendations else None,
        "planner_reasoning": bp.final_recommendations.get("planner_reasoning") if bp.final_recommendations else None,
    }
