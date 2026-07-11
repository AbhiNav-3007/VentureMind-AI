"""
VentureMind AI — Agent Reasoning & Execution Logger
=====================================================
Tracks per-agent timeline events: tool invocations, reasoning steps,
IBM service calls, token counts, and output summaries.
The timeline is stored in WorkflowState and broadcast via WebSocket.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ToolEvent:
    """A single tool call made by an agent."""
    tool_name: str                          # e.g. "IBM Granite", "Watson Discovery", "RAG", "FinCalc"
    tool_type: str                          # "llm" | "retrieval" | "calculation" | "service"
    ibm_service: str | None = None          # e.g. "watsonx.ai", "Watson Discovery", "IBM COS"
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float = 0.0
    input_summary: str = ""
    output_summary: str = ""
    tokens_consumed: int | None = None
    status: str = "pending"                 # "running" | "done" | "failed"
    error: str | None = None


@dataclass
class ReasoningStep:
    """A single reasoning step in the agent's chain-of-thought."""
    step_number: int
    description: str
    completed: bool = False
    result_summary: str = ""


@dataclass
class AgentTimeline:
    """
    Full execution timeline for one agent run.
    Sent to the frontend to display the Agent Reasoning Timeline panel.
    """
    agent_key: str                          # "planner" | "market" | "business" | "funding" | "strategy"
    agent_name: str
    agent_role: str
    agent_identity: str                     # One-sentence identity statement

    # Execution metadata
    startup_id: str = ""
    started_at: str = ""
    finished_at: str = ""
    total_duration_seconds: float = 0.0
    status: str = "pending"                 # "pending" | "running" | "done" | "failed"

    # What the agent received
    input_received: dict[str, Any] = field(default_factory=dict)

    # Reasoning chain
    reasoning_steps: list[ReasoningStep] = field(default_factory=list)

    # Tool calls made during execution
    tool_events: list[ToolEvent] = field(default_factory=list)

    # Output produced
    output_summary: str = ""
    output_keys: list[str] = field(default_factory=list)
    passed_to_next: str = ""               # what was forwarded to the next agent

    # Current live status
    current_task: str = ""
    current_tool: str = ""
    progress: float = 0.0

    # IBM service utilisation
    granite_calls: int = 0
    discovery_calls: int = 0
    rag_calls: int = 0
    total_tokens: int = 0

    # Planner validation result (if this agent was re-run)
    retry_count: int = 0
    retry_reason: str = ""

    def start(self, startup_id: str, input_context: dict) -> None:
        self.startup_id = startup_id
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.status = "running"
        self.input_received = input_context

    def finish(self, output_summary: str, output_keys: list[str], passed_to_next: str) -> None:
        self.finished_at = datetime.now(timezone.utc).isoformat()
        self.status = "done"
        self.output_summary = output_summary
        self.output_keys = output_keys
        self.passed_to_next = passed_to_next
        self.progress = 100.0
        if self.started_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.finished_at)
            self.total_duration_seconds = round((end - start).total_seconds(), 2)

    def fail(self, error: str) -> None:
        self.finished_at = datetime.now(timezone.utc).isoformat()
        self.status = "failed"
        self.output_summary = f"FAILED: {error}"

    def add_tool_event(
        self,
        tool_name: str,
        tool_type: str,
        ibm_service: str | None,
        input_summary: str,
    ) -> ToolEvent:
        """Open a new tool event and return it for later completion."""
        event = ToolEvent(
            tool_name=tool_name,
            tool_type=tool_type,
            ibm_service=ibm_service,
            started_at=datetime.now(timezone.utc).isoformat(),
            input_summary=input_summary,
            status="running",
        )
        self.tool_events.append(event)
        self.current_tool = tool_name

        # Increment service counters
        if tool_name == "IBM Granite":
            self.granite_calls += 1
        elif tool_name == "Watson Discovery":
            self.discovery_calls += 1
        elif tool_name == "RAG Pipeline":
            self.rag_calls += 1

        return event

    def complete_tool_event(
        self,
        event: ToolEvent,
        output_summary: str,
        tokens: int | None = None,
    ) -> None:
        """Mark a tool event as done."""
        event.finished_at = datetime.now(timezone.utc).isoformat()
        event.status = "done"
        event.output_summary = output_summary
        event.tokens_consumed = tokens
        if tokens:
            self.total_tokens += tokens
        if event.started_at:
            s = datetime.fromisoformat(event.started_at)
            e = datetime.fromisoformat(event.finished_at)
            event.duration_seconds = round((e - s).total_seconds(), 2)

    def fail_tool_event(self, event: ToolEvent, error: str) -> None:
        """Mark a tool event as failed."""
        event.finished_at = datetime.now(timezone.utc).isoformat()
        event.status = "failed"
        event.error = error

    def add_reasoning_step(self, step_number: int, description: str) -> None:
        self.reasoning_steps.append(ReasoningStep(
            step_number=step_number,
            description=description,
        ))

    def complete_reasoning_step(self, step_number: int, result: str) -> None:
        for step in self.reasoning_steps:
            if step.step_number == step_number:
                step.completed = True
                step.result_summary = result
                break

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_key": self.agent_key,
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "agent_identity": self.agent_identity,
            "startup_id": self.startup_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "total_duration_seconds": self.total_duration_seconds,
            "status": self.status,
            "current_task": self.current_task,
            "current_tool": self.current_tool,
            "progress": self.progress,
            "input_received": self.input_received,
            "reasoning_steps": [asdict(s) for s in self.reasoning_steps],
            "tool_events": [asdict(t) for t in self.tool_events],
            "output_summary": self.output_summary,
            "output_keys": self.output_keys,
            "passed_to_next": self.passed_to_next,
            "granite_calls": self.granite_calls,
            "discovery_calls": self.discovery_calls,
            "rag_calls": self.rag_calls,
            "total_tokens": self.total_tokens,
            "retry_count": self.retry_count,
            "retry_reason": self.retry_reason,
        }


def make_planner_timeline(startup_id: str) -> AgentTimeline:
    tl = AgentTimeline(
        agent_key="planner",
        agent_name="Planner & Orchestrator Agent",
        agent_role="Strategic planning, domain classification, workflow design, validation",
        agent_identity="I am the master orchestrator — I understand startup ideas, design execution plans, coordinate all agents, and validate final outputs.",
    )
    tl.add_reasoning_step(1, "Parsing and understanding the startup idea")
    tl.add_reasoning_step(2, "Classifying industry domain and business model type")
    tl.add_reasoning_step(3, "Identifying key challenges specific to this startup")
    tl.add_reasoning_step(4, "Creating execution instructions for each downstream agent")
    tl.add_reasoning_step(5, "Assessing feasibility score and urgency level")
    return tl


def make_market_timeline(startup_id: str) -> AgentTimeline:
    tl = AgentTimeline(
        agent_key="market",
        agent_name="Market Intelligence Agent",
        agent_role="Market research, competitor analysis, SWOT, customer personas",
        agent_identity="I am the market intelligence specialist — I research market size, analyze competitors, perform SWOT analysis, and build detailed customer personas using IBM Granite and RAG.",
    )
    tl.add_reasoning_step(1, "Querying RAG knowledge base for market intelligence")
    tl.add_reasoning_step(2, "Estimating TAM/SAM/SOM using bottom-up approach")
    tl.add_reasoning_step(3, "Identifying direct and indirect competitors")
    tl.add_reasoning_step(4, "Building SWOT from startup's perspective")
    tl.add_reasoning_step(5, "Creating psychographic customer personas")
    tl.add_reasoning_step(6, "Identifying market gaps and white-space opportunities")
    return tl


def make_business_timeline(startup_id: str) -> AgentTimeline:
    tl = AgentTimeline(
        agent_key="business",
        agent_name="Business & Finance Agent",
        agent_role="Business model canvas, lean canvas, financial projections, break-even",
        agent_identity="I am the business model architect — I design BMC, Lean Canvas, and Value Proposition Canvas, then use financial calculation utilities to produce realistic projections and break-even analysis.",
    )
    tl.add_reasoning_step(1, "Designing all 9 blocks of the Business Model Canvas")
    tl.add_reasoning_step(2, "Mapping Lean Canvas with unfair advantage focus")
    tl.add_reasoning_step(3, "Running financial calculation engine for cost estimation")
    tl.add_reasoning_step(4, "Building 3-year financial projections with growth assumptions")
    tl.add_reasoning_step(5, "Computing break-even point using FC/(P-VC) formula")
    tl.add_reasoning_step(6, "Calculating unit economics (CAC, LTV, payback period)")
    return tl


def make_funding_timeline(startup_id: str) -> AgentTimeline:
    tl = AgentTimeline(
        agent_key="funding",
        agent_name="Funding & Legal Agent",
        agent_role="Government schemes, funding stages, legal compliance, incubators",
        agent_identity="I am the funding and compliance specialist — I identify government schemes from the RAG knowledge base, filter eligible schemes, map the funding journey, and generate domain-specific legal compliance checklists.",
    )
    tl.add_reasoning_step(1, "Querying RAG knowledge base for domain-specific government schemes")
    tl.add_reasoning_step(2, "Filtering schemes by eligibility criteria")
    tl.add_reasoning_step(3, "Mapping funding journey from pre-seed to Series A")
    tl.add_reasoning_step(4, "Identifying most relevant incubators and accelerators")
    tl.add_reasoning_step(5, "Recommending optimal legal structure")
    tl.add_reasoning_step(6, "Generating compliance checklist with mandatory registrations")
    return tl


def make_strategy_timeline(startup_id: str) -> AgentTimeline:
    tl = AgentTimeline(
        agent_key="strategy",
        agent_name="Strategy & Report Agent",
        agent_role="GTM strategy, MVP recommendations, product roadmap, investor pitch, final blueprint",
        agent_identity="I am the strategic synthesis agent — I combine all prior agent outputs to create the go-to-market strategy, product roadmap, risk analysis, and investor pitch. I synthesize, not recreate.",
    )
    tl.add_reasoning_step(1, "Reviewing and cross-referencing all prior agent outputs")
    tl.add_reasoning_step(2, "Synthesizing executive summary from market + business + funding data")
    tl.add_reasoning_step(3, "Designing GTM phases aligned with customer personas")
    tl.add_reasoning_step(4, "Building product roadmap aligned with financial projections")
    tl.add_reasoning_step(5, "Performing risk assessment across 6 risk categories")
    tl.add_reasoning_step(6, "Crafting investor pitch with cross-referenced data points")
    return tl
