"""
VentureMind AI — LangGraph Orchestration Workflow (v2)
======================================================
True Agentic AI workflow with:
- Rich shared WorkflowState (TypedDict — required by LangGraph StateGraph)
- Conditional routing (Planner decides which agents run)
- Validation gate with retry logic (up to MAX_RETRIES)
- Per-agent AgentTimeline events broadcast via WebSocket
- Full context packages passed from Planner to each agent

LangGraph node contract:
  • Every node receives a WorkflowState dict (read-only by convention).
  • Every node RETURNS a plain dict containing only the keys it modified.
  • LangGraph merges returned dicts into the accumulated state automatically.
  • Nodes must NOT mutate the incoming state dict in-place.

Graph structure:
  planner → [conditional: which agents to run?]
         ↓
    market (if needed) → business (if needed) → funding (if needed) → strategy
         ↓
    validate_node ← [Planner reviews all outputs]
         ↓
    [if issues found] → retry_node → [re-run specific agent(s)]
         ↓
    aggregate → END
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import asdict
from typing import Any, Callable, Optional

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from app.agents.business_agent import BusinessFinanceAgent
from app.agents.funding_legal_agent import FundingLegalAgent
from app.agents.market_agent import MarketIntelligenceAgent
from app.agents.planner_agent import PlannerAgent, ValidationOutput
from app.agents.strategy_agent import StrategyReportAgent
from app.core.exceptions import OrchestratorError
from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 2  # Maximum number of retry passes per agent


# ── Workflow State (TypedDict — required by LangGraph StateGraph) ──────────────
#
# LangGraph's StateGraph requires a TypedDict (or Pydantic model) as its state
# schema. Using a plain @dataclass causes ainvoke() to return an AddableValuesDict
# (plain dict) instead of the dataclass instance, breaking attribute access.
#
# With TypedDict + total=False, nodes only need to return the keys they modified.

class WorkflowState(TypedDict, total=False):
    """
    Shared state dict passed through every LangGraph node.
    All fields are optional (total=False) so nodes can update only what they touch.
    """

    # ── User inputs ────────────────────────────────────────────────────────────
    startup_id: str
    idea: str
    industry: Optional[str]
    target_audience: Optional[str]
    country: Optional[str]
    budget: Optional[str]

    # ── Planner outputs ────────────────────────────────────────────────────────
    planner_output: dict
    agents_to_run: list
    context_for_agents: dict
    execution_plan: dict

    # ── Downstream agent outputs ───────────────────────────────────────────────
    market_output: dict
    business_output: dict
    funding_output: dict
    strategy_output: dict

    # ── Agent reasoning timelines ──────────────────────────────────────────────
    agent_timelines: dict

    # ── Validation state ───────────────────────────────────────────────────────
    validation_result: dict
    validation_passed: bool
    retry_count: int
    agents_to_retry: list
    retry_instructions: dict

    # ── Progress tracking ──────────────────────────────────────────────────────
    current_agent: str
    current_tool: str
    progress: float
    agent_statuses: dict
    errors: list

    # ── Final output ───────────────────────────────────────────────────────────
    is_complete: bool
    blueprint: dict

    # ── Live event callback (not serialised, injected at runtime) ─────────────
    progress_callback: Optional[Any]


def _default_state(
    startup_id: str,
    idea: str,
    industry: Optional[str],
    target_audience: Optional[str],
    country: Optional[str],
    budget: Optional[str],
    progress_callback: Optional[Callable],
) -> WorkflowState:
    """Build the initial WorkflowState dict with all default values."""
    return WorkflowState(
        startup_id=startup_id,
        idea=idea,
        industry=industry,
        target_audience=target_audience,
        country=country or "India",
        budget=budget,
        planner_output={},
        agents_to_run=["market", "business", "funding", "strategy"],
        context_for_agents={},
        execution_plan={},
        market_output={},
        business_output={},
        funding_output={},
        strategy_output={},
        agent_timelines={},
        validation_result={},
        validation_passed=False,
        retry_count=0,
        agents_to_retry=[],
        retry_instructions={},
        current_agent="Planner & Orchestrator Agent",
        current_tool="",
        progress=0.0,
        agent_statuses={
            "planner":    "pending",
            "market":     "pending",
            "business":   "pending",
            "funding":    "pending",
            "strategy":   "pending",
            "validation": "pending",
            "aggregate":  "pending",
        },
        errors=[],
        is_complete=False,
        blueprint={},
        progress_callback=progress_callback,
    )


# ── Routing Logic ──────────────────────────────────────────────────────────────

def _route_after_planner(state: WorkflowState) -> str:
    """
    Conditional router: after Planner runs, decide which agent goes first.
    The Planner sets agents_to_run; we always start with 'market' if present.
    """
    agents_to_run = state.get("agents_to_run", ["market", "business", "funding", "strategy"])
    if "market" in agents_to_run:
        return "market"
    if "business" in agents_to_run:
        return "business"
    if "funding" in agents_to_run:
        return "funding"
    return "strategy"


def _route_after_validate(state: WorkflowState) -> str:
    """
    After validation: if retry needed and under MAX_RETRIES → retry.
    Otherwise → aggregate.
    """
    if (
        not state.get("validation_passed", True)
        and state.get("agents_to_retry", [])
        and state.get("retry_count", 0) < MAX_RETRIES
    ):
        return "retry"
    return "aggregate"


def _route_after_retry(state: WorkflowState) -> str:
    """After retry, go back to validate."""
    return "validate"


# ── Agent Node Implementations ─────────────────────────────────────────────────
#
# IMPORTANT: Every node receives the accumulated state dict and must return
# a NEW dict containing ONLY the keys that changed. LangGraph merges these
# partial updates into the global state. Do NOT mutate `state` in-place.

async def _planner_node(state: WorkflowState) -> dict:
    """Planner & Orchestrator Agent — classifies the idea and builds execution plan."""
    await asyncio.sleep(2)
    agent_statuses = dict(state.get("agent_statuses", {}))
    agent_statuses["planner"] = "running"
    agent_timelines = dict(state.get("agent_timelines", {}))
    errors = list(state.get("errors", []))
    start = time.time()

    # Snapshot progress event before heavy work
    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback({**state, "current_agent": "Planner & Orchestrator Agent",
                                 "agent_statuses": agent_statuses, "progress": 5.0})

    try:
        agent = PlannerAgent()
        result = await agent.run(
            startup_id=state.get("startup_id", ""),
            idea=state.get("idea", ""),
            industry=state.get("industry"),
            target_audience=state.get("target_audience"),
            country=state.get("country", "India"),
            budget=state.get("budget"),
        )
        planner_output = asdict(result)
        agents_to_run = result.agents_to_run
        context_for_agents = result.context_for_agents
        execution_plan = result.execution_plan
        agent_timelines["planner"] = result.timeline
        agent_statuses["planner"] = "done"
        progress = 15.0
        logger.info("Planner node complete", elapsed=round(time.time() - start, 2))

    except Exception as exc:
        logger.error("Planner node failed", error=str(exc))
        agent_statuses["planner"] = "failed"
        errors.append(f"Planner: {str(exc)}")
        # Fallback: run all agents
        planner_output = {}
        agents_to_run = ["market", "business", "funding", "strategy"]
        context_for_agents = {}
        execution_plan = {}
        progress = 15.0

    updates = {
        "current_agent": "Planner & Orchestrator Agent",
        "agent_statuses": agent_statuses,
        "agent_timelines": agent_timelines,
        "errors": errors,
        "planner_output": planner_output,
        "agents_to_run": agents_to_run,
        "context_for_agents": context_for_agents,
        "execution_plan": execution_plan,
        "progress": progress,
    }

    if progress_callback:
        await progress_callback({**state, **updates})

    return updates


async def _market_node(state: WorkflowState) -> dict:
    """Market Intelligence Agent — market research, competitors, SWOT, personas."""
    await asyncio.sleep(2)
    agents_to_run = state.get("agents_to_run", [])
    agents_to_retry = state.get("agents_to_retry", [])
    agent_statuses = dict(state.get("agent_statuses", {}))
    agent_timelines = dict(state.get("agent_timelines", {}))
    errors = list(state.get("errors", []))

    if "market" not in agents_to_run and "market" not in agents_to_retry:
        # Skip if Planner didn't schedule this agent
        agent_statuses["market"] = "skipped"
        return {"agent_statuses": agent_statuses, "current_agent": "Market Intelligence Agent"}

    agent_statuses["market"] = "running"
    start = time.time()

    planner_output = state.get("planner_output", {})
    context_for_agents = state.get("context_for_agents", {})
    execution_plan = state.get("execution_plan", {})
    retry_instructions = state.get("retry_instructions", {})
    retry_inst = retry_instructions.get("market")

    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback({**state, "current_agent": "Market Intelligence Agent",
                                 "agent_statuses": agent_statuses, "progress": 20.0})

    try:
        agent = MarketIntelligenceAgent()
        result = await agent.run(
            startup_id=state.get("startup_id", ""),
            idea=state.get("idea", ""),
            domain=planner_output.get("domain", "Technology"),
            sub_domain=planner_output.get("sub_domain", ""),
            target_geography=planner_output.get("target_geography", "India"),
            planner_summary=planner_output.get("idea_summary", ""),
            competitive_landscape_hint=context_for_agents.get("competitive_landscape_hint", ""),
            execution_instructions=retry_inst or execution_plan.get("market_intelligence", ""),
        )
        market_output = asdict(result)
        agent_timelines["market"] = result.timeline
        agent_statuses["market"] = "done"
        progress = 35.0
        logger.info("Market node complete", elapsed=round(time.time() - start, 2))

    except Exception as exc:
        logger.error("Market node failed", error=str(exc))
        agent_statuses["market"] = "failed"
        errors.append(f"Market: {str(exc)}")
        market_output = {}
        progress = 35.0

    updates = {
        "current_agent": "Market Intelligence Agent",
        "agent_statuses": agent_statuses,
        "agent_timelines": agent_timelines,
        "errors": errors,
        "market_output": market_output,
        "progress": progress,
    }

    if progress_callback:
        await progress_callback({**state, **updates})

    return updates


async def _business_node(state: WorkflowState) -> dict:
    """Business & Finance Agent — business model canvas, financials, pricing."""
    await asyncio.sleep(2)
    agents_to_run = state.get("agents_to_run", [])
    agents_to_retry = state.get("agents_to_retry", [])
    agent_statuses = dict(state.get("agent_statuses", {}))
    agent_timelines = dict(state.get("agent_timelines", {}))
    errors = list(state.get("errors", []))

    if "business" not in agents_to_run and "business" not in agents_to_retry:
        agent_statuses["business"] = "skipped"
        return {"agent_statuses": agent_statuses, "current_agent": "Business & Finance Agent"}

    agent_statuses["business"] = "running"
    start = time.time()

    planner_output = state.get("planner_output", {})
    market_output = state.get("market_output", {})
    context_for_agents = state.get("context_for_agents", {})
    execution_plan = state.get("execution_plan", {})
    retry_instructions = state.get("retry_instructions", {})
    retry_inst = retry_instructions.get("business")

    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback({**state, "current_agent": "Business & Finance Agent",
                                 "agent_statuses": agent_statuses, "progress": 40.0})

    try:
        agent = BusinessFinanceAgent()
        result = await agent.run(
            startup_id=state.get("startup_id", ""),
            idea=state.get("idea", ""),
            domain=planner_output.get("domain", "Technology"),
            budget=state.get("budget"),
            market_summary=market_output.get("summary", ""),
            planner_summary=planner_output.get("idea_summary", ""),
            revenue_model_hint=context_for_agents.get("revenue_model_hint", ""),
            execution_instructions=retry_inst or execution_plan.get("business_finance", ""),
        )
        business_output = asdict(result)
        agent_timelines["business"] = result.timeline
        agent_statuses["business"] = "done"
        progress = 55.0
        logger.info("Business node complete", elapsed=round(time.time() - start, 2))

    except Exception as exc:
        logger.error("Business node failed", error=str(exc))
        agent_statuses["business"] = "failed"
        errors.append(f"Business: {str(exc)}")
        business_output = {}
        progress = 55.0

    updates = {
        "current_agent": "Business & Finance Agent",
        "agent_statuses": agent_statuses,
        "agent_timelines": agent_timelines,
        "errors": errors,
        "business_output": business_output,
        "progress": progress,
    }

    if progress_callback:
        await progress_callback({**state, **updates})

    return updates


async def _funding_node(state: WorkflowState) -> dict:
    """Funding & Legal Agent — government schemes, VC, legal compliance, IP."""
    await asyncio.sleep(2)
    agents_to_run = state.get("agents_to_run", [])
    agents_to_retry = state.get("agents_to_retry", [])
    agent_statuses = dict(state.get("agent_statuses", {}))
    agent_timelines = dict(state.get("agent_timelines", {}))
    errors = list(state.get("errors", []))

    if "funding" not in agents_to_run and "funding" not in agents_to_retry:
        agent_statuses["funding"] = "skipped"
        return {"agent_statuses": agent_statuses, "current_agent": "Funding & Legal Agent"}

    agent_statuses["funding"] = "running"
    start = time.time()

    planner_output = state.get("planner_output", {})
    business_output = state.get("business_output", {})
    context_for_agents = state.get("context_for_agents", {})
    execution_plan = state.get("execution_plan", {})
    retry_instructions = state.get("retry_instructions", {})
    retry_inst = retry_instructions.get("funding")

    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback({**state, "current_agent": "Funding & Legal Agent",
                                 "agent_statuses": agent_statuses, "progress": 60.0})

    try:
        agent = FundingLegalAgent()
        result = await agent.run(
            startup_id=state.get("startup_id", ""),
            idea=state.get("idea", ""),
            domain=planner_output.get("domain", "Technology"),
            country=state.get("country", "India"),
            business_summary=business_output.get("summary", ""),
            compliance_hint=context_for_agents.get("compliance_hint", ""),
            execution_instructions=retry_inst or execution_plan.get("funding_legal", ""),
        )
        funding_output = asdict(result)
        agent_timelines["funding"] = result.timeline
        agent_statuses["funding"] = "done"
        progress = 72.0
        logger.info("Funding node complete", elapsed=round(time.time() - start, 2))

    except Exception as exc:
        logger.error("Funding node failed", error=str(exc))
        agent_statuses["funding"] = "failed"
        errors.append(f"Funding: {str(exc)}")
        funding_output = {}
        progress = 72.0

    updates = {
        "current_agent": "Funding & Legal Agent",
        "agent_statuses": agent_statuses,
        "agent_timelines": agent_timelines,
        "errors": errors,
        "funding_output": funding_output,
        "progress": progress,
    }

    if progress_callback:
        await progress_callback({**state, **updates})

    return updates


async def _strategy_node(state: WorkflowState) -> dict:
    """Strategy & Report Agent — GTM, roadmap, risk analysis, investor pitch."""
    await asyncio.sleep(2)
    agents_to_run = state.get("agents_to_run", [])
    agents_to_retry = state.get("agents_to_retry", [])
    agent_statuses = dict(state.get("agent_statuses", {}))
    agent_timelines = dict(state.get("agent_timelines", {}))
    errors = list(state.get("errors", []))

    if "strategy" not in agents_to_run and "strategy" not in agents_to_retry:
        agent_statuses["strategy"] = "skipped"
        return {"agent_statuses": agent_statuses, "current_agent": "Strategy & Report Agent"}

    agent_statuses["strategy"] = "running"
    start = time.time()

    planner_output = state.get("planner_output", {})
    context_for_agents = state.get("context_for_agents", {})
    execution_plan = state.get("execution_plan", {})
    retry_instructions = state.get("retry_instructions", {})
    retry_inst = retry_instructions.get("strategy")

    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback({**state, "current_agent": "Strategy & Report Agent",
                                 "agent_statuses": agent_statuses, "progress": 78.0})

    try:
        agent = StrategyReportAgent()
        result = await agent.run(
            startup_id=state.get("startup_id", ""),
            idea=state.get("idea", ""),
            domain=planner_output.get("domain", "Technology"),
            # Pass FULL agent outputs, not just summaries
            planner_output=planner_output,
            market_output=state.get("market_output", {}),
            business_output=state.get("business_output", {}),
            funding_output=state.get("funding_output", {}),
            gtm_hint=context_for_agents.get("gtm_hint", ""),
            execution_instructions=retry_inst or execution_plan.get("strategy_report", ""),
        )
        strategy_output = asdict(result)
        agent_timelines["strategy"] = result.timeline
        agent_statuses["strategy"] = "done"
        progress = 88.0
        logger.info("Strategy node complete", elapsed=round(time.time() - start, 2))

    except Exception as exc:
        logger.error("Strategy node failed", error=str(exc))
        agent_statuses["strategy"] = "failed"
        errors.append(f"Strategy: {str(exc)}")
        strategy_output = {}
        progress = 88.0

    updates = {
        "current_agent": "Strategy & Report Agent",
        "agent_statuses": agent_statuses,
        "agent_timelines": agent_timelines,
        "errors": errors,
        "strategy_output": strategy_output,
        "progress": progress,
    }

    if progress_callback:
        await progress_callback({**state, **updates})

    return updates


async def _validate_node(state: WorkflowState) -> dict:
    """
    Validation gate: Planner reviews all outputs and decides if quality is acceptable.
    If issues found, marks agents_to_retry with specific retry instructions.
    """
    await asyncio.sleep(2)
    agent_statuses = dict(state.get("agent_statuses", {}))
    agent_statuses["validation"] = "running"

    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback({**state, "current_agent": "Planner (Validation)",
                                 "agent_statuses": agent_statuses, "progress": 92.0})

    try:
        planner = PlannerAgent()
        val: ValidationOutput = await planner.validate(
            startup_id=state.get("startup_id", ""),
            market_output=state.get("market_output", {}),
            business_output=state.get("business_output", {}),
            funding_output=state.get("funding_output", {}),
            strategy_output=state.get("strategy_output", {}),
            planner_output=state.get("planner_output", {}),
        )
        validation_result = asdict(val)
        validation_passed = val.validation_passed
        agents_to_retry = val.agents_to_retry
        retry_instructions = val.retry_instructions

        if validation_passed:
            agent_statuses["validation"] = "done"
            logger.info(
                "Validation passed",
                quality=val.quality_score,
                summary=val.validation_summary[:100],
            )
        else:
            agent_statuses["validation"] = "retry_needed"
            logger.info(
                "Validation found issues",
                to_retry=val.agents_to_retry,
                issues=val.issues_found[:3],
            )

    except Exception as exc:
        logger.warning("Validation failed, auto-passing", error=str(exc))
        validation_result = {}
        validation_passed = True
        agents_to_retry = []
        retry_instructions = {}
        agent_statuses["validation"] = "done"

    updates = {
        "current_agent": "Planner (Validation)",
        "agent_statuses": agent_statuses,
        "validation_result": validation_result,
        "validation_passed": validation_passed,
        "agents_to_retry": agents_to_retry,
        "retry_instructions": retry_instructions,
        "progress": 92.0,
    }

    if progress_callback:
        await progress_callback({**state, **updates})

    return updates


async def _retry_node(state: WorkflowState) -> dict:
    """
    Retry gate: re-runs agents flagged by Planner validation.
    Increments retry_count to prevent infinite loops.

    NOTE: Because LangGraph nodes cannot call other nodes directly, we re-invoke
    the agent functions here and collect their partial update dicts, then merge
    them into a single return dict.
    """
    retry_count = state.get("retry_count", 0) + 1
    agents_to_retry = state.get("agents_to_retry", [])
    agent_statuses = dict(state.get("agent_statuses", {}))
    agent_statuses["retry"] = "running"

    logger.info(
        "Retry node starting",
        pass_num=retry_count,
        agents=agents_to_retry,
    )

    # Merge the updated retry_count into a working copy so child calls see it
    working_state: WorkflowState = {**state, "retry_count": retry_count,
                                    "agent_statuses": agent_statuses}  # type: ignore[assignment]

    # Accumulated partial updates from retried agents
    accumulated: dict = {
        "retry_count": retry_count,
        "agent_statuses": agent_statuses,
        "agents_to_retry": [],  # Clear — will be re-set by next validation if needed
    }

    for agent_key in agents_to_retry:
        if agent_key == "market":
            partial = await _market_node(working_state)
        elif agent_key == "business":
            partial = await _business_node(working_state)
        elif agent_key == "funding":
            partial = await _funding_node(working_state)
        elif agent_key == "strategy":
            partial = await _strategy_node(working_state)
        else:
            continue

        # Merge partial updates into accumulated dict and working state
        accumulated.update(partial)
        working_state = {**working_state, **partial}  # type: ignore[assignment]

    accumulated["agent_statuses"] = dict(working_state.get("agent_statuses", {}))
    accumulated["agent_statuses"]["retry"] = "done"

    return accumulated


async def _aggregate_node(state: WorkflowState) -> dict:
    """
    Final aggregation: assembles the complete blueprint from all agent outputs.
    """
    agent_statuses = dict(state.get("agent_statuses", {}))
    agent_statuses["aggregate"] = "running"

    blueprint = _assemble_blueprint(state)
    agent_statuses["aggregate"] = "done"

    updates = {
        "current_agent": "Planner (Final Assembly)",
        "agent_statuses": agent_statuses,
        "blueprint": blueprint,
        "is_complete": True,
        "progress": 100.0,
    }

    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback({**state, **updates})

    logger.info("Workflow complete", startup_id=state.get("startup_id"))
    return updates


def _assemble_blueprint(state: WorkflowState) -> dict[str, Any]:
    """
    Assemble the final blueprint by merging all agent outputs.
    Includes agent timelines for the reasoning panel.
    """
    market_output = state.get("market_output", {})
    business_output = state.get("business_output", {})
    funding_output = state.get("funding_output", {})
    strategy_output = state.get("strategy_output", {})
    planner_output = state.get("planner_output", {})

    return {
        "startup_id": state.get("startup_id"),
        "idea": state.get("idea"),

        # From Strategy Agent
        "executive_summary": strategy_output.get("executive_summary", {}),
        "marketing_strategy": strategy_output.get("go_to_market_strategy", {}),
        "product_roadmap": strategy_output.get("product_roadmap", []),
        "risk_analysis": strategy_output.get("risk_analysis", []),
        "investor_pitch": strategy_output.get("investor_pitch", {}),
        "mvp_recommendations": strategy_output.get("mvp_recommendations", {}),
        "final_recommendations": strategy_output.get("final_recommendations", []),
        "success_metrics": strategy_output.get("success_metrics", []),

        # From Market Agent
        "market_research": market_output.get("market_overview", {}),
        "competitor_analysis": market_output.get("competitors", []),
        "swot_analysis": market_output.get("swot", {}),
        "customer_personas": market_output.get("customer_personas", []),
        "market_opportunities": market_output.get("market_opportunities", []),
        "market_gaps": market_output.get("market_gaps", []),
        "watson_discovery_insights": market_output.get("watson_discovery_insights", []),

        # From Business Agent
        "business_model": business_output.get("business_model_canvas", {}),
        "lean_canvas": business_output.get("lean_canvas", {}),
        "value_proposition_canvas": business_output.get("value_proposition_canvas", {}),
        "financial_plan": {
            "projections": business_output.get("financial_projections", {}),
            "operational_costs": business_output.get("operational_costs", []),
            "break_even": business_output.get("break_even_analysis", {}),
            "pricing": business_output.get("pricing_strategy", {}),
            "unit_economics": business_output.get("unit_economics", {}),
            "calculated_financials": business_output.get("calculated_financials", {}),
        },

        # From Funding Agent
        "funding_opportunities": {
            "stages": funding_output.get("funding_stages", []),
            "government_schemes": funding_output.get("government_schemes", []),
            "incubators": funding_output.get("incubators_accelerators", []),
            "angel_networks": funding_output.get("angel_networks", []),
            "vc_firms": funding_output.get("vc_firms", []),
            "rag_retrieved_schemes": funding_output.get("rag_retrieved_schemes", []),
        },
        "legal_compliance": funding_output.get("legal_compliance", {}),
        "funding_roadmap": funding_output.get("funding_roadmap", []),

        # From Planner
        "domain": planner_output.get("domain", ""),
        "sub_domain": planner_output.get("sub_domain", ""),
        "feasibility_score": planner_output.get("feasibility_score", 0),
        "urgency_level": planner_output.get("urgency_level", "medium"),
        "key_challenges": planner_output.get("key_challenges", []),
        "planner_reasoning": planner_output.get("planner_reasoning", ""),

        # Validation & Quality
        "validation": state.get("validation_result", {}),
        "retry_count": state.get("retry_count", 0),

        # Agent Reasoning Timelines (for frontend panel)
        "agent_timelines": state.get("agent_timelines", {}),
        "agent_statuses": state.get("agent_statuses", {}),
    }


# ── Graph Construction ─────────────────────────────────────────────────────────

def build_workflow_graph() -> Any:
    """
    Build and compile the LangGraph state machine.

    Graph:
      planner → [conditional] → market → business → funding → strategy
              ↓
           validate ← [conditional after validate: retry or aggregate]
              ↓
           retry (if needed) → validate (loop, max 2)
              ↓
           aggregate → END
    """
    graph = StateGraph(WorkflowState)

    # Register all nodes
    graph.add_node("planner", _planner_node)
    graph.add_node("market", _market_node)
    graph.add_node("business", _business_node)
    graph.add_node("funding", _funding_node)
    graph.add_node("strategy", _strategy_node)
    graph.add_node("validate", _validate_node)
    graph.add_node("retry", _retry_node)
    graph.add_node("aggregate", _aggregate_node)

    # Entry point
    graph.set_entry_point("planner")

    # Planner → conditional routing to first scheduled agent
    graph.add_conditional_edges(
        "planner",
        _route_after_planner,
        {
            "market": "market",
            "business": "business",
            "funding": "funding",
            "strategy": "strategy",
        },
    )

    # Sequential agent chain (each agent runs in order)
    graph.add_edge("market", "business")
    graph.add_edge("business", "funding")
    graph.add_edge("funding", "strategy")
    graph.add_edge("strategy", "validate")

    # Conditional routing after validation
    graph.add_conditional_edges(
        "validate",
        _route_after_validate,
        {
            "retry": "retry",
            "aggregate": "aggregate",
        },
    )

    # Retry loops back to validate (prevent infinite loops via MAX_RETRIES check)
    graph.add_conditional_edges(
        "retry",
        _route_after_retry,
        {"validate": "validate"},
    )

    # Terminal node
    graph.add_edge("aggregate", END)

    return graph.compile()


# ── Public Runner ──────────────────────────────────────────────────────────────

async def run_workflow(
    startup_id: str,
    idea: str,
    industry: str | None = None,
    target_audience: str | None = None,
    country: str | None = None,
    budget: str | None = None,
    progress_callback: Callable | None = None,
) -> WorkflowState:
    """
    Execute the full VentureMind AI agentic workflow.

    Returns:
        Completed WorkflowState dict with blueprint, validation result, and agent timelines.
    """
    initial_state = _default_state(
        startup_id=startup_id,
        idea=idea,
        industry=industry,
        target_audience=target_audience,
        country=country,
        budget=budget,
        progress_callback=progress_callback,
    )

    workflow = build_workflow_graph()
    final_state: WorkflowState = await workflow.ainvoke(initial_state)

    if not final_state.get("is_complete"):
        raise OrchestratorError(
            "Workflow did not complete",
            {
                "errors": final_state.get("errors", []),
                "statuses": final_state.get("agent_statuses", {}),
            },
        )

    return final_state
