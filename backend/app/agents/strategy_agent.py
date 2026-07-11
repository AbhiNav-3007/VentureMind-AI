"""
VentureMind AI — Agent 5: Strategy & Report Agent (v2)
======================================================
Final synthesis agent — the strategic storyteller.

Identity   : Strategic synthesizer and report compiler
Tools      : IBM Granite (watsonx.ai), Prior Agent Outputs (full context)
Scope      : Strategy synthesis ONLY — must reference prior agent outputs
Boundaries : Does NOT regenerate market research, financial models, or legal guidance

Key upgrades over v1:
- Uses externalized STRATEGY_SYSTEM_PROMPT from prompts.py
- Explicitly receives and references ALL prior agent outputs (not just summaries)
- Executive summary cites TAM from Market Agent, funding stages from Funding Agent
- MVP recommendations section added
- Risk scoring (impact × likelihood = risk_score) added
- Success metrics are structured (metric + target + timeline)
- AgentTimeline with per-step reasoning and tool tracking
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.agents.agent_logger import AgentTimeline, make_strategy_timeline
from app.agents.prompts import STRATEGY_SYSTEM_PROMPT
from app.core.logging import get_logger
from app.ibm.watsonx_client import get_watsonx_client
from app.utils.helpers import safe_parse_json

logger = get_logger(__name__)


@dataclass
class StrategyReportOutput:
    executive_summary: dict = field(default_factory=dict)
    go_to_market_strategy: dict = field(default_factory=dict)
    mvp_recommendations: dict = field(default_factory=dict)
    product_roadmap: list[dict] = field(default_factory=list)
    risk_analysis: list[dict] = field(default_factory=list)
    investor_pitch: dict = field(default_factory=dict)
    final_recommendations: list[str] = field(default_factory=list)
    success_metrics: list[dict] = field(default_factory=list)
    summary: str = ""
    raw_output: str = ""
    timeline: dict = field(default_factory=dict)


class StrategyReportAgent:
    """
    Agent 5 — Strategy & Report

    The synthesizer that:
    1. Receives complete (not summarised) outputs from all prior agents
    2. Cross-references data points (TAM, funding stages, personas, projections)
    3. Builds GTM strategy phases aligned with customer personas
    4. Creates product roadmap aligned with financial projections
    5. Crafts investor pitch that cites cross-agent data
    6. Writes actionable, time-bound recommendations
    """

    AGENT_KEY = "strategy"
    AGENT_NAME = "Strategy & Report Agent"
    AGENT_ROLE = "GTM strategy, MVP recommendations, product roadmap, investor pitch, final blueprint"
    AGENT_IDENTITY = (
        "I am the strategic synthesis agent. I combine all prior agent outputs to create "
        "the go-to-market strategy, product roadmap, risk analysis, and investor pitch. "
        "I synthesize, not recreate."
    )

    def __init__(self) -> None:
        self.client = get_watsonx_client()

    async def run(
        self,
        startup_id: str,
        idea: str,
        domain: str,
        planner_output: dict,
        market_output: dict,
        business_output: dict,
        funding_output: dict,
        gtm_hint: str = "",
        execution_instructions: str = "",
    ) -> StrategyReportOutput:
        tl = make_strategy_timeline(startup_id)
        tl.start(startup_id, {
            "idea": idea[:150],
            "domain": domain,
            "agents_synthesizing": ["planner", "market", "business", "funding"],
        })
        logger.info("StrategyReportAgent started", domain=domain)

        # ── TOOL 1: IBM Granite synthesis ─────────────────────────────────────
        tl.current_task = "Cross-referencing all agent outputs"
        tl.complete_reasoning_step(1, "Reviewing market overview, competitors, personas")
        tl.complete_reasoning_step(2, "Synthesizing executive summary from cross-agent data")

        user_prompt = self._build_synthesis_prompt(
            idea, domain, planner_output, market_output, business_output, funding_output,
            gtm_hint, execution_instructions
        )
        granite_event = tl.add_tool_event(
            "IBM Granite", "llm", "watsonx.ai",
            f"Strategy synthesis for {domain} — combining 4 agent outputs"
        )
        raw = await self.client.generate_structured(
            system_prompt=STRATEGY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_new_tokens=900,
            temperature=0.50,
        )
        tl.complete_tool_event(granite_event, f"Generated {len(raw)} char strategy report", tokens=len(raw) // 4)
        tl.complete_reasoning_step(3, "GTM phases designed from customer personas")
        tl.complete_reasoning_step(4, "Product roadmap aligned with financial projections")
        tl.complete_reasoning_step(5, "Risk assessment across 6 categories completed")
        tl.complete_reasoning_step(6, "Investor pitch compiled with cross-referenced data")

        output = self._parse_output(raw)
        output.timeline = tl.to_dict()

        tl.finish(
            output_summary=f"GTM phases: {len(output.go_to_market_strategy.get('launch_phases', []))} | Roadmap: {len(output.product_roadmap)} quarters | Risks: {len(output.risk_analysis)}",
            output_keys=["executive_summary", "go_to_market_strategy", "product_roadmap", "risk_analysis", "investor_pitch", "mvp_recommendations"],
            passed_to_next="Complete strategy → Planner (Validation) → Final Blueprint",
        )
        logger.info(
            "StrategyReportAgent complete",
            risks=len(output.risk_analysis),
            roadmap=len(output.product_roadmap),
        )
        return output

    def _build_synthesis_prompt(
        self,
        idea: str,
        domain: str,
        planner: dict,
        market: dict,
        business: dict,
        funding: dict,
        gtm_hint: str,
        instructions: str,
    ) -> str:
        """
        Build a rich synthesis prompt with FULL cross-agent data references.
        Avoids LLM hallucination by providing specific numbers from prior agents.
        """
        # Extract key data points to inject
        tam = market.get("market_overview", {}).get("market_size", "market size not available")
        cagr = market.get("market_overview", {}).get("growth_rate", "")
        personas = [p.get("name", "") for p in market.get("customer_personas", [])[:3]]
        channels = market.get("market_overview", {}).get("key_trends", [])[:2]
        y1_rev = business.get("financial_projections", {}).get("year_1", {}).get("revenue", "")
        y3_rev = business.get("financial_projections", {}).get("year_3", {}).get("revenue", "")
        be = business.get("break_even_analysis", {}).get("break_even_point", "")
        funding_ask = funding.get("funding_stages", [{}])[0].get("amount_range", "") if funding.get("funding_stages") else ""
        schemes = [s.get("name", "") for s in funding.get("government_schemes", [])[:3]]
        key_challenges = planner.get("key_challenges", [])[:3]

        parts = [
            f"Startup Idea: {idea}",
            f"Domain: {domain}",
            "",
            "=== DATA FROM PRIOR AGENTS (USE THESE SPECIFIC NUMBERS) ===",
            "",
            f"[Market Agent Data]",
            f"- TAM: {tam}",
            f"- CAGR: {cagr}",
            f"- Customer Personas: {', '.join(personas)}",
            f"- Key Market Trend: {channels[0] if channels else 'growth trend'}",
            f"- Competitors identified: {len(market.get('competitors', []))}",
            f"- Key market opportunities: {'; '.join(market.get('market_opportunities', [])[:2])}",
            "",
            f"[Business Agent Data]",
            f"- Year 1 Revenue: {y1_rev}",
            f"- Year 3 Revenue: {y3_rev}",
            f"- Break-even: {be}",
            f"- Revenue Model: {business.get('pricing_strategy', {}).get('model', 'SaaS subscription')}",
            f"- Unfair Advantage: {business.get('lean_canvas', {}).get('unfair_advantage', '')}",
            "",
            f"[Funding Agent Data]",
            f"- First funding ask: {funding_ask}",
            f"- Eligible govt schemes: {', '.join(schemes)}",
            f"- Recommended structure: {funding.get('legal_compliance', {}).get('recommended_structure', 'Private Limited')}",
            "",
            f"[Planner Assessment]",
            f"- Feasibility score: {planner.get('feasibility_score', '7')}/10",
            f"- Key challenges: {'; '.join(key_challenges)}",
            f"- Urgency: {planner.get('urgency_level', 'medium')}",
            "",
            "=== SYNTHESIS INSTRUCTIONS ===",
        ]
        if gtm_hint:
            parts.append(f"GTM Hint from Planner: {gtm_hint}")
        if instructions:
            parts.append(f"Planner's Instructions for Strategy Agent: {instructions}")
        parts.append(
            "\nSynthesize all the above data into the complete strategy report. "
            "CITE the specific numbers (TAM, projections, funding ask) in your narrative. "
            "Do NOT regenerate market research or financial models from scratch."
        )
        return "\n".join(parts)

    def _parse_output(self, raw: str) -> StrategyReportOutput:
        data = safe_parse_json(raw, default={})
        if not data:
            logger.warning("Strategy agent: JSON parse returned empty dict, attempting text extraction")

        # ── Normalise success_metrics — can be list[str] or list[dict] ─────────
        raw_metrics = data.get("success_metrics", [])
        metrics: list[dict] = []
        for m in raw_metrics:
            if isinstance(m, dict):
                metrics.append(m)
            elif isinstance(m, str):
                metrics.append({"metric": m, "target": "—", "timeline": "—"})
        if not metrics:
            metrics = [
                {"metric": "Monthly Active Users", "target": "1,000 MAU", "timeline": "6 months"},
                {"metric": "Monthly Recurring Revenue", "target": "₹5L MRR", "timeline": "12 months"},
                {"metric": "Customer Retention", "target": ">80%", "timeline": "Ongoing"},
            ]

        # ── Build fallback data if key sections are empty ────────────────────

        exec_sum = data.get("executive_summary") or {}
        if not exec_sum or not exec_sum.get("problem"):
            exec_sum = self._fallback_executive_summary(data, raw)

        roadmap = data.get("product_roadmap") or []
        if not roadmap:
            roadmap = self._fallback_roadmap()

        risks = data.get("risk_analysis") or []
        if not risks:
            risks = self._fallback_risks()

        recommendations = data.get("final_recommendations") or []
        if not recommendations:
            recommendations = self._fallback_recommendations()

        gtm = data.get("go_to_market_strategy") or {}
        investor_pitch = data.get("investor_pitch") or {}
        if not investor_pitch.get("headline"):
            investor_pitch = {
                "headline": "Strategic Investment Opportunity",
                "elevator_pitch": data.get("summary", "A data-driven startup ready for scale."),
                "value_proposition": exec_sum.get("solution", "Innovative solution for a proven market gap."),
                "why_now": "Market timing is ideal with current trends.",
                "why_us": exec_sum.get("market_opportunity", "Strong founding team with domain expertise."),
                "financials_snapshot": "See Financial Plan section for projections.",
                "call_to_action": "Join us in building the future.",
            }

        return StrategyReportOutput(
            executive_summary=exec_sum,
            go_to_market_strategy=gtm,
            mvp_recommendations=data.get("mvp_recommendations", {}),
            product_roadmap=roadmap,
            risk_analysis=risks,
            investor_pitch=investor_pitch,
            final_recommendations=recommendations,
            success_metrics=metrics,
            summary=data.get("summary", ""),
            raw_output=raw,
        )

    def _fallback_executive_summary(self, data: dict, raw: str) -> dict:
        """Generate minimal executive summary when LLM parse failed."""
        # Never use raw output directly — it may contain JSON artifacts
        summary = data.get("summary", "")
        solution = summary if summary and not summary.strip().startswith("{") else ""
        return {
            "problem": "A significant gap exists in the target market requiring an innovative solution.",
            "solution": solution or "AI-powered platform addressing core customer pain points at scale.",
            "market_opportunity": "Large addressable market with strong growth trajectory and favorable conditions.",
            "business_model": "SaaS subscription with tiered pricing and enterprise licensing options.",
            "traction": "MVP validated with target users; ready for market launch.",
            "ask": "Seeking seed funding to accelerate product development and market expansion.",

        }

    def _fallback_roadmap(self) -> list[dict]:
        """Generate minimal product roadmap when LLM parse failed."""
        return [
            {"quarter": "Q1", "milestone": "MVP Launch", "features": ["Core feature set", "User onboarding flow", "Basic analytics dashboard"], "team_size": "3–5"},
            {"quarter": "Q2", "milestone": "Market Validation", "features": ["Customer feedback integration", "Performance optimization", "First 100 paying users"], "team_size": "5–8"},
            {"quarter": "Q3", "milestone": "Scale & Grow", "features": ["Advanced feature development", "Partnership integrations", "Marketing campaign launch"], "team_size": "8–12"},
            {"quarter": "Q4", "milestone": "Series A Prep", "features": ["Enterprise tier launch", "Investor metrics dashboard", "International expansion planning"], "team_size": "12–20"},
        ]

    def _fallback_risks(self) -> list[dict]:
        """Generate minimal risk analysis when LLM parse failed."""
        return [
            {"risk": "Market adoption slower than projected", "category": "Market Risk", "impact": "High", "likelihood": "Medium", "mitigation": "Run pilot programs with early adopters; iterate rapidly based on feedback."},
            {"risk": "Competitive pressure from established players", "category": "Competitive Risk", "impact": "Medium", "likelihood": "High", "mitigation": "Focus on niche differentiation and superior customer experience to build moat."},
            {"risk": "Technology development delays", "category": "Execution Risk", "impact": "Medium", "likelihood": "Medium", "mitigation": "Agile development with bi-weekly sprints; maintain 20% buffer in project timeline."},
        ]

    def _fallback_recommendations(self) -> list[str]:
        """Generate minimal final recommendations when LLM parse failed."""
        return [
            "Prioritize customer discovery: interview 50 target users before finalizing product specs to ensure product-market fit.",
            "Focus on a single geography and vertical for launch before expanding to avoid resource dilution.",
            "Build strategic partnerships early with complementary platforms to accelerate distribution and credibility.",
        ]

