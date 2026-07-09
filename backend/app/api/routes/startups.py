"""
VentureMind AI — Startup Submission API Routes
POST /api/v1/startups/generate  → launch the multi-agent workflow
GET  /api/v1/startups/{id}      → poll startup status
GET  /api/v1/startups/          → list all past blueprints
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import raise_not_found
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.agent_log import AgentLog
from app.models.blueprint import Blueprint
from app.models.startup import StartupIdea
from app.services.orchestrator_service import run_startup_workflow

logger = get_logger(__name__)
router = APIRouter(prefix="/startups", tags=["Startups"])


# ── Request / Response Schemas ─────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    idea: str = Field(..., min_length=10, max_length=2000, description="Raw startup idea text")
    industry: str | None = Field(None, max_length=200)
    target_audience: str | None = Field(None, max_length=500)
    country: str | None = Field(default="India", max_length=100)
    budget: str | None = Field(None, max_length=100)


class StartupStatusResponse(BaseModel):
    id: str
    status: str
    idea_text: str
    created_at: str
    updated_at: str
    agent_statuses: list[dict] = []


class BlueprintSummaryResponse(BaseModel):
    id: str
    startup_id: str
    domain: str | None
    created_at: str
    pdf_url: str | None


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_blueprint(
    payload: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Submit a startup idea and kick off the autonomous agent workflow.
    Returns the startup ID immediately; poll /startups/{id} for status.
    """
    # Persist startup idea
    startup = StartupIdea(
        idea_text=payload.idea,
        industry=payload.industry,
        target_audience=payload.target_audience,
        country=payload.country or "India",
        budget=payload.budget,
        status="pending",
    )
    db.add(startup)
    await db.flush()  # Get the ID before background task

    startup_id = str(startup.id)
    logger.info("Startup idea created", startup_id=startup_id)

    # Enqueue workflow as background task
    background_tasks.add_task(
        run_startup_workflow,
        startup_id=startup_id,
        idea=payload.idea,
        industry=payload.industry,
        target_audience=payload.target_audience,
        country=payload.country,
        budget=payload.budget,
    )

    return {
        "startup_id": startup_id,
        "status": "pending",
        "message": "Blueprint generation started. Use the startup_id to poll progress.",
    }


@router.get("/{startup_id}/status")
async def get_startup_status(
    startup_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Poll the status of a startup workflow and its per-agent progress."""
    result = await db.execute(
        select(StartupIdea).where(StartupIdea.id == uuid.UUID(startup_id))
    )
    startup = result.scalar_one_or_none()
    if not startup:
        raise_not_found("Startup idea")

    # Fetch agent logs
    logs_result = await db.execute(
        select(AgentLog)
        .where(AgentLog.startup_id == uuid.UUID(startup_id))
        .order_by(AgentLog.created_at)
    )
    logs = logs_result.scalars().all()

    return {
        "id": str(startup.id),
        "status": startup.status,
        "idea_text": startup.idea_text,
        "created_at": startup.created_at.isoformat(),
        "updated_at": startup.updated_at.isoformat(),
        "agents": [
            {
                "agent_name": log.agent_name,
                "agent_role": log.agent_role,
                "status": log.status,
                "current_task": log.current_task,
                "progress": log.progress,
                "execution_time_seconds": log.execution_time_seconds,
                "output_summary": log.output_summary,
            }
            for log in logs
        ],
    }


@router.get("/{startup_id}/blueprint")
async def get_blueprint(
    startup_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve the completed blueprint for a given startup ID."""
    result = await db.execute(
        select(Blueprint).where(Blueprint.startup_id == uuid.UUID(startup_id))
    )
    blueprint = result.scalar_one_or_none()
    if not blueprint:
        raise_not_found("Blueprint")

    return {
        "id": str(blueprint.id),
        "startup_id": startup_id,
        "executive_summary": blueprint.executive_summary,
        "market_research": blueprint.market_research,
        "competitor_analysis": blueprint.competitor_analysis,
        "swot_analysis": blueprint.swot_analysis,
        "customer_personas": blueprint.customer_personas,
        "business_model": blueprint.business_model,
        "lean_canvas": blueprint.lean_canvas,
        "financial_plan": blueprint.financial_plan,
        "funding_opportunities": blueprint.funding_opportunities,
        "legal_compliance": blueprint.legal_compliance,
        "marketing_strategy": blueprint.marketing_strategy,
        "product_roadmap": blueprint.product_roadmap,
        "risk_analysis": blueprint.risk_analysis,
        "investor_pitch": blueprint.investor_pitch,
        "final_recommendations": blueprint.final_recommendations,
        "pdf_url": blueprint.pdf_url,
        "created_at": blueprint.created_at.isoformat(),
    }


@router.get("/")
async def list_blueprints(
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """List all startup blueprints (paginated)."""
    result = await db.execute(
        select(StartupIdea).order_by(StartupIdea.created_at.desc()).limit(limit).offset(offset)
    )
    startups = result.scalars().all()
    return {
        "items": [
            {
                "id": str(s.id),
                "idea_text": s.idea_text[:120] + "..." if len(s.idea_text) > 120 else s.idea_text,
                "industry": s.industry,
                "status": s.status,
                "country": s.country,
                "created_at": s.created_at.isoformat(),
            }
            for s in startups
        ],
        "total": len(startups),
    }


@router.post("/{startup_id}/stop")
async def stop_generation(
    startup_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Stop/cancel a running startup blueprint generation."""
    from app.services.orchestrator_service import cancel_startup_workflow
    await cancel_startup_workflow(startup_id)
    return {"status": "cancelled", "message": "Blueprint generation stopped by user."}

