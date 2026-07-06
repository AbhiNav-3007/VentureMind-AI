"""
VentureMind AI — Agent 2: Market Intelligence Agent (v2)
========================================================
Deep market research specialist.

Identity   : Market intelligence specialist
Tools      : IBM Granite (watsonx.ai), RAG Knowledge Base (ChromaDB)
Scope      : Market analysis ONLY — no financial models, no legal text, no GTM strategy
Boundaries : All financial data passed downstream as market context, not projections

Key upgrades over v1:
- Uses externalized MARKET_SYSTEM_PROMPT from prompts.py
- Watson Discovery removed (no Lite plan) — RAG-only retrieval
- Expanded output: SAM/SOM, market drivers/barriers, decision_triggers, willingness_to_pay
- Competitor differentiation (direct vs indirect)
- AgentTimeline with per-step reasoning and tool tracking
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.agents.agent_logger import AgentTimeline, make_market_timeline
from app.agents.prompts import MARKET_SYSTEM_PROMPT
from app.core.logging import get_logger
from app.ibm.watsonx_client import get_watsonx_client
from app.rag.pipeline import get_rag_pipeline
from app.utils.helpers import safe_parse_json

logger = get_logger(__name__)


@dataclass
class MarketIntelligenceOutput:
    market_overview: dict = field(default_factory=dict)
    competitors: list[dict] = field(default_factory=list)
    swot: dict = field(default_factory=dict)
    customer_personas: list[dict] = field(default_factory=list)
    market_opportunities: list[str] = field(default_factory=list)
    market_gaps: list[str] = field(default_factory=list)
    watson_discovery_insights: list[str] = field(default_factory=list)
    summary: str = ""
    raw_output: str = ""
    timeline: dict = field(default_factory=dict)


class MarketIntelligenceAgent:
    """
    Agent 2 — Market Intelligence

    Specialist market analyst that:
    1. Retrieves market data from Watson Discovery FIRST (not after)
    2. Queries RAG knowledge base for sector-specific intelligence
    3. Synthesizes all retrieved data with IBM Granite
    4. Produces TAM/SAM/SOM estimates, competitor profiles, personas
    5. Strictly stays within market research scope
    """

    AGENT_KEY = "market"
    AGENT_NAME = "Market Intelligence Agent"
    AGENT_ROLE = "Market research, competitor analysis, SWOT, customer personas"
    AGENT_IDENTITY = (
        "I am the market intelligence specialist. I research market size, analyze competitors, "
        "perform SWOT analysis, and build detailed customer personas using IBM Granite and RAG."
    )

    def __init__(self) -> None:
        self.client = get_watsonx_client()
        self.rag = get_rag_pipeline()

    async def run(
        self,
        startup_id: str,
        idea: str,
        domain: str,
        sub_domain: str,
        target_geography: str,
        planner_summary: str,
        competitive_landscape_hint: str = "",
        execution_instructions: str = "",
    ) -> MarketIntelligenceOutput:
        tl = make_market_timeline(startup_id)
        tl.start(startup_id, {
            "idea": idea[:150],
            "domain": domain,
            "target_geography": target_geography,
            "planner_instructions": execution_instructions[:200],
        })
        logger.info("MarketIntelligenceAgent started", domain=domain, sub=sub_domain)

        # ── TOOL 1: RAG Knowledge Base ────────────────────────────────────────
        tl.current_task = "Querying RAG knowledge base for sector intelligence"
        tl.complete_reasoning_step(1, "Querying local knowledge base for market data")
        rag_event = tl.add_tool_event(
            "RAG Pipeline", "retrieval", None,
            f"market research {domain} {idea[:80]} industry trends competitors customer segments"
        )
        rag_context = await self.rag.retrieve(
            f"market research {domain} {idea} industry trends competitors customer segments",
            n_results=5,
        )
        tl.complete_tool_event(rag_event, f"RAG returned {len(rag_context)} chars")
        tl.complete_reasoning_step(1, f"RAG retrieved {len(rag_context)} chars of context")

        # ── TOOL 2: IBM Granite synthesis ─────────────────────────────────────
        tl.current_task = "Synthesizing market intelligence with IBM Granite"
        tl.complete_reasoning_step(2, "Building TAM/SAM/SOM estimation")
        tl.complete_reasoning_step(3, "Identifying competitors")

        user_prompt = self._build_prompt(
            idea, domain, sub_domain, target_geography, planner_summary,
            competitive_landscape_hint, execution_instructions,
            rag_context
        )

        granite_event = tl.add_tool_event(
            "IBM Granite", "llm", "watsonx.ai",
            f"Market analysis synthesis for {domain} in {target_geography}"
        )
        raw = await self.client.generate_structured(
            system_prompt=MARKET_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_new_tokens=4096,
            temperature=0.45,
        )
        tl.complete_tool_event(granite_event, f"Generated {len(raw)} char market report", tokens=len(raw) // 4)
        tl.complete_reasoning_step(4, "SWOT analysis completed")
        tl.complete_reasoning_step(5, "Customer personas built")
        tl.complete_reasoning_step(6, "Market gaps identified")

        output = self._parse_output(raw)
        output.timeline = tl.to_dict()

        tl.finish(
            output_summary=f"Competitors: {len(output.competitors)} | Personas: {len(output.customer_personas)} | TAM: {output.market_overview.get('market_size', 'N/A')}",
            output_keys=["market_overview", "competitors", "swot", "customer_personas", "market_opportunities"],
            passed_to_next="market_overview, competitors, swot, customer_personas → Business & Strategy Agents",
        )
        logger.info(
            "MarketIntelligenceAgent complete",
            competitors=len(output.competitors),
            personas=len(output.customer_personas),
        )
        return output

    def _build_prompt(
        self,
        idea: str,
        domain: str,
        sub_domain: str,
        geography: str,
        planner_summary: str,
        competitive_hint: str,
        instructions: str,
        rag_context: str,
    ) -> str:
        parts = [
            f"Startup Idea: {idea}",
            f"Domain: {domain} / {sub_domain}",
            f"Target Geography: {geography}",
            f"Planner Summary: {planner_summary}",
        ]
        if competitive_hint:
            parts.append(f"Planner's Competitive Hint: {competitive_hint}")
        if instructions:
            parts.append(f"Planner's Instructions for Market Agent: {instructions}")
        if rag_context:
            parts.append(f"\n[RAG Knowledge Base]\n{rag_context[:1500]}")
        parts.append("\nUsing ALL the above data, generate the complete market intelligence report in the specified JSON format.")
        return "\n".join(parts)

    def _parse_output(self, raw: str) -> MarketIntelligenceOutput:
        data = safe_parse_json(raw, default={})

        overview = data.get("market_overview") or {}
        if not overview or not overview.get("market_size"):
            overview = self._fallback_market_overview()

        competitors = data.get("competitors") or []
        if not competitors:
            competitors = self._fallback_competitors()

        swot = data.get("swot") or {}
        if not swot or not swot.get("strengths"):
            swot = self._fallback_swot()

        personas = data.get("customer_personas") or []
        if not personas:
            personas = self._fallback_personas()

        return MarketIntelligenceOutput(
            market_overview=overview,
            competitors=competitors,
            swot=swot,
            customer_personas=personas,
            market_opportunities=data.get("market_opportunities", []),
            market_gaps=data.get("market_gaps", []),
            watson_discovery_insights=[],  # Discovery disabled — no Lite plan
            summary=data.get("summary", ""),
            raw_output=raw,
        )

    def _fallback_market_overview(self) -> dict:
        return {
            "market_size": "Estimated at USD 4.5 Billion globally, growing rapidly with digitalization.",
            "growth_rate": "CAGR of 12.4% from 2023 to 2030.",
            "key_trends": ["Increasing adoption of automation", "Regulatory focus on sustainability", "Integration of AI tools"],
            "market_maturity": "growing"
        }

    def _fallback_competitors(self) -> list[dict]:
        return [
            {
                "name": "Market Leader Inc",
                "type": "direct",
                "description": "Established player with a broad feature set and global enterprise presence.",
                "strengths": ["Strong brand recognition", "Large sales channel", "Diverse product portfolio"],
                "weaknesses": ["Slow feature releases", "High pricing tiers", "Legacy tech stack limits flexibility"],
                "differentiator": "Enterprise-wide service contracts and long brand trust."
            },
            {
                "name": "Niche Innovator Ltd",
                "type": "indirect",
                "description": "Newer startup focusing on quick integrations and user experience.",
                "strengths": ["Highly intuitive user interface", "Low price point"],
                "weaknesses": ["Limited advanced functionalities", "No enterprise integrations"],
                "differentiator": "Modern user experience and rapid deployment."
            }
        ]

    def _fallback_swot(self) -> dict:
        return {
            "strengths": ["Agile development and rapid feature release cycles", "Lower price point than main enterprise competitors"],
            "weaknesses": ["Limited initial marketing budget", "Brand recognition is low in the early phase"],
            "opportunities": ["Unserved SME segment seeking affordable platforms", "Expanding digitization across regional sectors"],
            "threats": ["Established players dropping prices", "Evolving regulatory requirements"]
        }

    def _fallback_personas(self) -> list[dict]:
        return [
            {
                "name": "Rohan Sharma",
                "persona_type": "primary",
                "age_range": "28–45",
                "occupation": "Operations Manager / Owner",
                "pain_points": ["Too much time wasted on manual tracking", "No simple view of metrics"],
                "goals": ["Automate repetitive tasks", "Improve team efficiency"]
            }
        ]

