"""
VentureMind AI — Agent 1: Planner & Orchestrator Agent (v2)
===========================================================
The master decision-maker of VentureMind AI.

Identity   : Strategic intelligence, domain classification, workflow design, validation
Tools      : IBM Granite (watsonx.ai), RAG Knowledge Base
Scope      : Startup understanding, planning, coordination, and final validation ONLY.
Boundaries : Does NOT generate financial figures, legal text, or marketing copy.

Key upgrades over v1:
- Uses externalized prompts from prompts.py
- Dynamic agent routing (agents_to_run list)
- Validation pass with retry decision
- Detailed AgentTimeline logging
- Context packages for downstream agents
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.agents.agent_logger import AgentTimeline, make_planner_timeline
from app.agents.prompts import PLANNER_SYSTEM_PROMPT, PLANNER_VALIDATION_PROMPT
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.ibm.watsonx_client import get_watsonx_client
from app.rag.pipeline import get_rag_pipeline
from app.utils.helpers import safe_parse_json

logger = get_logger(__name__)


@dataclass
class PlannerOutput:
    idea_summary: str = ""
    domain: str = ""
    sub_domain: str = ""
    business_model_type: str = ""
    target_geography: str = ""
    target_audience: str = ""
    key_challenges: list[str] = field(default_factory=list)
    feasibility_score: float = 5.0
    urgency_level: str = "medium"
    hardware_dependency: bool = False
    requires_compliance: bool = False
    execution_plan: dict[str, str] = field(default_factory=dict)
    agents_to_run: list[str] = field(default_factory=lambda: ["market", "business", "funding", "strategy"])
    context_for_agents: dict[str, str] = field(default_factory=dict)
    planner_reasoning: str = ""
    raw_output: str = ""
    timeline: dict = field(default_factory=dict)


@dataclass
class ValidationOutput:
    validation_passed: bool = False
    quality_score: float = 5.0
    issues_found: list[str] = field(default_factory=list)
    agents_to_retry: list[str] = field(default_factory=list)
    retry_instructions: dict[str, str | None] = field(default_factory=dict)
    validation_summary: str = ""


class PlannerAgent:
    """
    Agent 1 — Planner & Orchestrator

    Master decision-maker that:
    1. Understands and classifies the startup idea
    2. Dynamically determines which agents should run
    3. Provides rich context to each downstream agent
    4. Validates all outputs and requests retries if needed
    5. Maintains an AgentTimeline for the reasoning panel
    """

    # Agent identity constants
    AGENT_KEY = "planner"
    AGENT_NAME = "Planner & Orchestrator Agent"
    AGENT_ROLE = "Strategic planning, domain classification, workflow design, final validation"
    AGENT_IDENTITY = (
        "I am the master orchestrator. I understand startup ideas, classify domains, "
        "design execution plans, coordinate all agents, and validate final outputs."
    )

    def __init__(self) -> None:
        self.client = get_watsonx_client()
        self.rag = get_rag_pipeline()

    async def run(
        self,
        startup_id: str,
        idea: str,
        industry: str | None = None,
        target_audience: str | None = None,
        country: str | None = None,
        budget: str | None = None,
    ) -> PlannerOutput:
        """
        Plan phase: understand the idea and build the execution plan.
        """
        tl = make_planner_timeline(startup_id)
        tl.start(startup_id, {
            "idea": idea[:200],
            "industry": industry,
            "target_audience": target_audience,
            "country": country,
            "budget": budget,
        })

        logger.info("PlannerAgent.run() started", startup_id=startup_id)

        # ── Step 1-2: RAG retrieval for domain context ────────────────────────
        tl.current_task = "Retrieving domain context from knowledge base"
        tl.add_reasoning_step(1, "Parsing and understanding the startup idea")
        rag_event = tl.add_tool_event(
            "RAG Pipeline", "retrieval", None,
            f"startup idea classification: {idea[:100]}"
        )
        context = await self.rag.retrieve(
            f"startup domain classification business model {idea}",
            n_results=3,
        )
        tl.complete_tool_event(rag_event, f"Retrieved {len(context)} chars of context")
        tl.complete_reasoning_step(1, f"Idea parsed: '{idea[:80]}…'")

        # ── Step 3-5: IBM Granite call ────────────────────────────────────────
        tl.current_task = "Calling IBM Granite to classify domain and build execution plan"
        tl.add_reasoning_step(2, "Classifying industry domain and business model type")
        tl.add_reasoning_step(3, "Identifying key challenges specific to this startup")
        tl.add_reasoning_step(4, "Creating execution instructions for each downstream agent")
        tl.add_reasoning_step(5, "Assessing feasibility score and urgency level")

        user_prompt = self._build_prompt(idea, industry, target_audience, country, budget, context)
        granite_event = tl.add_tool_event(
            "IBM Granite", "llm", "watsonx.ai",
            f"Classify domain + plan for: {idea[:100]}"
        )
        raw = await self.client.generate_structured(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_new_tokens=400,
            temperature=0.35,
        )
        tl.complete_tool_event(granite_event, f"Generated {len(raw)} char plan", tokens=len(raw) // 4)
        tl.complete_reasoning_step(2, "Domain classified")
        tl.complete_reasoning_step(3, "Challenges identified")
        tl.complete_reasoning_step(4, "Execution plan created")
        tl.complete_reasoning_step(5, "Feasibility assessed")

        output = self._parse_output(raw)
        output.timeline = tl.to_dict()

        tl.finish(
            output_summary=f"Domain: {output.domain} | Score: {output.feasibility_score} | Agents: {output.agents_to_run}",
            output_keys=["domain", "execution_plan", "agents_to_run", "context_for_agents"],
            passed_to_next=f"Context packages for {len(output.agents_to_run)} agents",
        )

        logger.info(
            "PlannerAgent complete",
            domain=output.domain,
            agents=output.agents_to_run,
            score=output.feasibility_score,
        )
        return output

    async def validate(
        self,
        startup_id: str,
        market_output: dict,
        business_output: dict,
        funding_output: dict,
        strategy_output: dict,
        planner_output: dict,
    ) -> ValidationOutput:
        """
        Validation phase: review all agent outputs and decide on completeness.
        """
        logger.info("PlannerAgent.validate() started", startup_id=startup_id)

        # Build validation prompt with all outputs
        outputs_summary = f"""
MARKET INTELLIGENCE OUTPUT:
- market_overview keys: {list(market_output.get('market_overview', {}).keys())}
- competitors count: {len(market_output.get('competitors', []))}
- customer_personas count: {len(market_output.get('customer_personas', []))}
- swot keys: {list(market_output.get('swot', {}).keys())}
- has_summary: {bool(market_output.get('summary'))}

BUSINESS & FINANCE OUTPUT:
- business_model_canvas filled: {bool(market_output.get('business_model_canvas') or business_output.get('business_model_canvas'))}
- financial_projections keys: {list(business_output.get('financial_projections', {}).keys())}
- break_even_analysis: {bool(business_output.get('break_even_analysis'))}
- unit_economics: {bool(business_output.get('unit_economics'))}

FUNDING & LEGAL OUTPUT:
- government_schemes count: {len(funding_output.get('government_schemes', []))}
- legal_compliance: {bool(funding_output.get('legal_compliance'))}
- funding_stages count: {len(funding_output.get('funding_stages', []))}
- incubators count: {len(funding_output.get('incubators_accelerators', []))}

STRATEGY & REPORT OUTPUT:
- executive_summary: {bool(strategy_output.get('executive_summary'))}
- go_to_market_strategy: {bool(strategy_output.get('go_to_market_strategy'))}
- product_roadmap count: {len(strategy_output.get('product_roadmap', []))}
- investor_pitch: {bool(strategy_output.get('investor_pitch'))}
- risk_analysis count: {len(strategy_output.get('risk_analysis', []))}
"""
        granite_event_val = None
        try:
            raw = await self.client.generate_structured(
                system_prompt=PLANNER_VALIDATION_PROMPT,
                user_prompt=f"Startup Context:\n{planner_output.get('idea_summary', '')}\n\nAgent Outputs:\n{outputs_summary}\n\nPerform validation.",
                max_new_tokens=300,
                temperature=0.2,
            )
            data = safe_parse_json(raw, default={})
            
            # Normalize retry keys to canonical forms
            raw_retries = data.get("agents_to_retry", [])
            retries = []
            for r in raw_retries:
                r_lower = str(r).lower()
                if "market" in r_lower:
                    retries.append("market")
                elif "business" in r_lower or "finance" in r_lower:
                    retries.append("business")
                elif "funding" in r_lower or "legal" in r_lower:
                    retries.append("funding")
                elif "strategy" in r_lower or "report" in r_lower:
                    retries.append("strategy")

            raw_instructions = data.get("retry_instructions", {})
            instructions = {}
            for k, v in raw_instructions.items():
                k_lower = str(k).lower()
                if "market" in k_lower:
                    instructions["market"] = v
                elif "business" in k_lower or "finance" in k_lower:
                    instructions["business"] = v
                elif "funding" in k_lower or "legal" in k_lower:
                    instructions["funding"] = v
                elif "strategy" in k_lower or "report" in k_lower:
                    instructions["strategy"] = v

            return ValidationOutput(
                validation_passed=data.get("validation_passed", True),
                quality_score=data.get("quality_score", 7.0),
                issues_found=data.get("issues_found", []),
                agents_to_retry=retries,
                retry_instructions=instructions,
                validation_summary=data.get("validation_summary", "Validation complete"),
            )
        except Exception as exc:
            logger.warning("Planner validation failed, proceeding with defaults", error=str(exc))
            return ValidationOutput(
                validation_passed=True,
                quality_score=7.0,
                validation_summary=f"Auto-passed (validation LLM failed: {str(exc)[:100]})",
            )

    def _build_prompt(
        self,
        idea: str,
        industry: str | None,
        audience: str | None,
        country: str | None,
        budget: str | None,
        context: str,
    ) -> str:
        lines = [f"Startup Idea: {idea}"]
        if industry:
            lines.append(f"Industry Hint (user-provided): {industry}")
        if audience:
            lines.append(f"Target Audience (user-provided): {audience}")
        if country:
            lines.append(f"Country: {country}")
        if budget:
            lines.append(f"Budget: {budget}")
        if context:
            lines.append(f"\nKnowledge Base Context:\n{context}")
        lines.append("\nAnalyse this startup idea and produce the complete planning JSON as specified.")
        return "\n".join(lines)

    def _parse_output(self, raw: str) -> PlannerOutput:
        data = safe_parse_json(raw, default={})
        return PlannerOutput(
            idea_summary=data.get("idea_summary", ""),
            domain=data.get("domain", "Technology"),
            sub_domain=data.get("sub_domain", ""),
            business_model_type=data.get("business_model_type", "B2B"),
            target_geography=data.get("target_geography", "India"),
            target_audience=data.get("target_audience", ""),
            key_challenges=data.get("key_challenges", []),
            feasibility_score=float(data.get("feasibility_score", 5.0)),
            urgency_level=data.get("urgency_level", "medium"),
            hardware_dependency=bool(data.get("hardware_dependency", False)),
            requires_compliance=bool(data.get("requires_compliance", False)),
            execution_plan=data.get("execution_plan", {}),
            agents_to_run=data.get("agents_to_run", ["market", "business", "funding", "strategy"]),
            context_for_agents=data.get("context_for_agents", {}),
            planner_reasoning=data.get("planner_reasoning", ""),
            raw_output=raw,
        )
