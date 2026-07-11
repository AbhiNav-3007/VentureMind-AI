"""
VentureMind AI — Orchestrator Service (v2)
==========================================
Upgraded to broadcast rich WebSocket events including:
- current_tool (for live tool indicator on frontend)
- agent_timelines (for reasoning panel)
- validation result
- retry events
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import OrchestratorError
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.langgraph.workflow import WorkflowState, run_workflow
from app.models.agent_log import AgentLog
from app.models.blueprint import Blueprint
from app.models.startup import StartupIdea
from app.services.websocket_manager import ws_manager

logger = get_logger(__name__)

# ── Agent metadata ─────────────────────────────────────────────────────────────
AGENT_META = {
    "planner":    ("Planner & Orchestrator Agent",  "Strategic planning, domain classification, workflow design"),
    "market":     ("Market Intelligence Agent",     "Market research, competitor analysis, SWOT, customer personas"),
    "business":   ("Business & Finance Agent",      "BMC, lean canvas, financial projections, unit economics"),
    "funding":    ("Funding & Legal Agent",         "Government schemes, legal compliance, funding stages"),
    "strategy":   ("Strategy & Report Agent",       "GTM strategy, product roadmap, investor pitch, blueprint"),
    "validation": ("Planner (Validation)",          "Blueprint quality validation and retry decisions"),
    "aggregate":  ("Planner (Final Assembly)",      "Blueprint assembly and compilation"),
}


cancelled_tasks: set[str] = set()


async def cancel_startup_workflow(startup_id: str) -> None:
    """Flag a startup workflow for cancellation."""
    cancelled_tasks.add(startup_id)
    logger.info("Startup workflow flagged for cancellation", startup_id=startup_id)


async def run_startup_workflow(
    startup_id: str,
    idea: str,
    industry: str | None = None,
    target_audience: str | None = None,
    country: str | None = None,
    budget: str | None = None,
) -> None:
    """
    Background task: runs the full agentic LangGraph workflow,
    persists progress + timelines to the DB, and broadcasts rich WS events.
    """
    logger.info("Orchestrator v2 started", startup_id=startup_id)
    start_time = time.time()

    async with AsyncSessionLocal() as db:
        try:
            await _update_startup_status(db, startup_id, "running")
            await _init_agent_logs(db, startup_id)

            async def progress_callback(state: WorkflowState) -> None:
                if startup_id in cancelled_tasks:
                    cancelled_tasks.discard(startup_id)
                    raise OrchestratorError("Workflow cancelled by user")
                await _handle_progress(db, startup_id, state)

            final_state = await run_workflow(
                startup_id=startup_id,
                idea=idea,
                industry=industry,
                target_audience=target_audience,
                country=country,
                budget=budget,
                progress_callback=progress_callback,
            )

            await _persist_blueprint(db, startup_id, final_state.get("blueprint", {}))
            await _update_startup_status(db, startup_id, "done")

            elapsed = round(time.time() - start_time, 2)
            logger.info("Orchestrator complete", startup_id=startup_id, elapsed=elapsed)

            await ws_manager.broadcast(startup_id, {
                "event": "complete",
                "startup_id": startup_id,
                "elapsed": elapsed,
                "validation": final_state.get("validation_result", {}),
                "retry_count": final_state.get("retry_count", 0),
                "agent_statuses": final_state.get("agent_statuses", {}),
            })

        except Exception as exc:
            logger.error("Orchestrator failed", startup_id=startup_id, error=str(exc))
            await _update_startup_status(db, startup_id, "failed")
            await ws_manager.broadcast(startup_id, {
                "event": "error",
                "startup_id": startup_id,
                "error": str(exc),
            })


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _update_startup_status(db: AsyncSession, startup_id: str, status: str) -> None:
    result = await db.execute(
        select(StartupIdea).where(StartupIdea.id == uuid.UUID(startup_id))
    )
    startup = result.scalar_one_or_none()
    if startup:
        startup.status = status
        startup.updated_at = datetime.now(timezone.utc)
        await db.commit()


async def _init_agent_logs(db: AsyncSession, startup_id: str) -> None:
    for key, (name, role) in AGENT_META.items():
        log = AgentLog(
            startup_id=uuid.UUID(startup_id),
            agent_name=name,
            agent_role=role,
            status="pending",
        )
        db.add(log)
    await db.commit()


async def _handle_progress(db: AsyncSession, startup_id: str, state: WorkflowState) -> None:
    """
    Update agent log with rich timeline data and broadcast enriched WS event.
    """
    current_agent = state.get("current_agent", "")
    agent_key = _resolve_agent_key(current_agent)
    agent_statuses = state.get("agent_statuses", {})
    agent_status = agent_statuses.get(agent_key, "running")
    agent_name, agent_role = AGENT_META.get(agent_key, (current_agent, ""))

    result = await db.execute(
        select(AgentLog).where(
            AgentLog.startup_id == uuid.UUID(startup_id),
            AgentLog.agent_name == agent_name,
        )
    )
    log = result.scalar_one_or_none()
    agent_timelines = state.get("agent_timelines", {})
    progress = state.get("progress", 0.0)
    current_tool = state.get("current_tool", "")
    validation_result = state.get("validation_result")
    retry_count = state.get("retry_count", 0)

    if log:
        log.status = agent_status
        log.progress = progress
        log.current_task = current_agent

        if agent_status == "running":
            log.started_at = datetime.now(timezone.utc)
            log.current_task = f"{agent_name} — {current_agent}"
        elif agent_status in ("done", "skipped"):
            log.finished_at = datetime.now(timezone.utc)
            if log.started_at:
                log.execution_time_seconds = (
                    log.finished_at - log.started_at
                ).total_seconds()
            log.progress = 100.0
            # Store output summary from timeline
            tl = agent_timelines.get(agent_key, {})
            if tl.get("output_summary"):
                log.output_summary = tl["output_summary"]

        # Store metadata with timeline
        tl = agent_timelines.get(agent_key)
        if tl:
            log.agent_metadata = {
                "tool_events": tl.get("tool_events", [])[-3:],  # last 3 tool calls
                "granite_calls": tl.get("granite_calls", 0),
                "discovery_calls": tl.get("discovery_calls", 0),
                "total_tokens": tl.get("total_tokens", 0),
            }
        await db.commit()

    # Broadcast rich WebSocket event
    await ws_manager.broadcast(startup_id, {
        "event": "progress",
        "startup_id": startup_id,
        "current_agent": current_agent,
        "current_tool": current_tool,
        "progress": progress,
        "agent_statuses": agent_statuses,
        # Send timeline for the current agent
        "active_timeline": agent_timelines.get(agent_key, {}),
        "validation": validation_result if validation_result else None,
        "retry_count": retry_count,
    })


async def _persist_blueprint(db: AsyncSession, startup_id: str, data: dict) -> None:
    existing = await db.execute(
        select(Blueprint).where(Blueprint.startup_id == uuid.UUID(startup_id))
    )
    bp = existing.scalar_one_or_none()
    if bp is None:
        bp = Blueprint(startup_id=uuid.UUID(startup_id))
        db.add(bp)

    bp.executive_summary = data.get("executive_summary")
    bp.market_research = data.get("market_research")
    bp.competitor_analysis = data.get("competitor_analysis")
    bp.swot_analysis = data.get("swot_analysis")
    bp.customer_personas = data.get("customer_personas")
    bp.business_model = data.get("business_model")
    bp.lean_canvas = data.get("lean_canvas")
    bp.financial_plan = data.get("financial_plan")
    bp.funding_opportunities = data.get("funding_opportunities")
    bp.legal_compliance = data.get("legal_compliance")
    bp.marketing_strategy = data.get("marketing_strategy")
    bp.product_roadmap = data.get("product_roadmap")
    bp.risk_analysis = data.get("risk_analysis")
    bp.investor_pitch = data.get("investor_pitch")
    bp.final_recommendations = {
        "recommendations": data.get("final_recommendations"),
        "success_metrics": data.get("success_metrics"),
        "mvp_recommendations": data.get("mvp_recommendations"),
        "validation": data.get("validation"),
        "agent_timelines": data.get("agent_timelines"),
        "feasibility_score": data.get("feasibility_score"),
        "urgency_level": data.get("urgency_level"),
        "planner_reasoning": data.get("planner_reasoning"),
        "watson_discovery_insights": data.get("watson_discovery_insights"),
        "market_gaps": data.get("market_gaps"),
    }

    await db.commit()
    logger.info("Blueprint v2 persisted", startup_id=startup_id)


def _resolve_agent_key(current_agent: str) -> str:
    mapping = {
        "Planner & Orchestrator Agent": "planner",
        "Market Intelligence Agent": "market",
        "Business & Finance Agent": "business",
        "Funding & Legal Agent": "funding",
        "Strategy & Report Agent": "strategy",
        "Planner (Validation)": "validation",
        "Planner (Final Assembly)": "aggregate",
    }
    for key_pattern, agent_key in mapping.items():
        if key_pattern in current_agent:
            return agent_key
    return "planner"
