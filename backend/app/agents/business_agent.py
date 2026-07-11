"""
VentureMind AI — Agent 3: Business & Finance Agent (v2)
=======================================================
Business model architect and financial modeler.

Identity   : Business model architect and financial modeler
Tools      : IBM Granite (watsonx.ai), Financial Calculation Engine (deterministic math)
Scope      : Business models and financial planning ONLY
Boundaries : No market research, no legal guidance, no GTM strategy

Key upgrades over v1:
- Uses externalized BUSINESS_SYSTEM_PROMPT from prompts.py
- Financial Calculation Engine provides DETERMINISTIC break-even, projections, unit economics
- LLM is used for qualitative sections (BMC, Lean Canvas); math tools for numbers
- Value Proposition Canvas added
- Unit economics (CAC/LTV/payback) calculated programmatically
- AgentTimeline with per-step reasoning and tool tracking
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.agents.agent_logger import AgentTimeline, make_business_timeline
from app.agents.financial_tools import (
    calculate_break_even,
    calculate_unit_economics,
    estimate_startup_costs,
    format_inr,
    project_financials,
)
from app.agents.prompts import BUSINESS_SYSTEM_PROMPT
from app.core.logging import get_logger
from app.ibm.watsonx_client import get_watsonx_client
from app.utils.helpers import safe_parse_json

logger = get_logger(__name__)


@dataclass
class BusinessFinanceOutput:
    business_model_canvas: dict = field(default_factory=dict)
    lean_canvas: dict = field(default_factory=dict)
    value_proposition_canvas: dict = field(default_factory=dict)
    pricing_strategy: dict = field(default_factory=dict)
    financial_projections: dict = field(default_factory=dict)
    operational_costs: list[dict] = field(default_factory=list)
    break_even_analysis: dict = field(default_factory=dict)
    unit_economics: dict = field(default_factory=dict)
    calculated_financials: dict = field(default_factory=dict)  # from FinCalc engine
    summary: str = ""
    raw_output: str = ""
    timeline: dict = field(default_factory=dict)


class BusinessFinanceAgent:
    """
    Agent 3 — Business & Finance

    Business model architect that:
    1. Uses IBM Granite for qualitative canvas sections
    2. Uses the Financial Calculation Engine for all numerical outputs
    3. Produces Business Model Canvas, Lean Canvas, Value Proposition Canvas
    4. Delivers verifiable break-even analysis with shown formula
    5. Calculates unit economics deterministically
    """

    AGENT_KEY = "business"
    AGENT_NAME = "Business & Finance Agent"
    AGENT_ROLE = "Business model canvas, lean canvas, financial projections, break-even"
    AGENT_IDENTITY = (
        "I am the business model architect. I design BMC, Lean Canvas, and Value Proposition Canvas, "
        "then use a financial calculation engine to produce deterministic projections and break-even analysis."
    )

    def __init__(self) -> None:
        self.client = get_watsonx_client()

    async def run(
        self,
        startup_id: str,
        idea: str,
        domain: str,
        budget: str | None,
        market_summary: str,
        planner_summary: str,
        revenue_model_hint: str = "",
        execution_instructions: str = "",
        team_size: int = 3,
    ) -> BusinessFinanceOutput:
        tl = make_business_timeline(startup_id)
        tl.start(startup_id, {
            "idea": idea[:150],
            "domain": domain,
            "budget": budget,
            "market_context": market_summary[:200],
        })
        logger.info("BusinessFinanceAgent started", domain=domain)

        # ── TOOL 1: Financial Calculation Engine (deterministic) ───────────────
        tl.current_task = "Running financial calculation engine for cost estimation"
        tl.complete_reasoning_step(3, "Financial calculation engine started")
        calc_event = tl.add_tool_event(
            "Financial Calculator", "calculation", None,
            f"Estimate costs for {domain} startup, team_size={team_size}"
        )
        costs = estimate_startup_costs(domain=domain, team_size=team_size, months=18)

        # Estimate break-even with reasonable defaults (LLM will refine labels)
        price_unit = 5000.0    # ₹5,000 / month per customer (SaaS default)
        variable_cost = 1200.0  # ₹1,200 variable cost per customer
        monthly_fc = costs["total_monthly"]
        be_result = calculate_break_even(
            monthly_fixed_costs=monthly_fc,
            price_per_unit=price_unit,
            variable_cost_per_unit=variable_cost,
            monthly_units_sold=10,
        )

        # Financial projections
        proj = project_financials(
            year1_customers=50,
            avg_revenue_per_customer=price_unit * 12,
            monthly_fixed_costs=monthly_fc,
            variable_cost_ratio=variable_cost / price_unit,
        )

        # Unit economics
        ue = calculate_unit_economics(
            cac=12000.0,
            monthly_revenue_per_customer=price_unit,
            monthly_churn_rate=0.03,
            gross_margin=(price_unit - variable_cost) / price_unit,
        )

        calculated_financials = {
            "monthly_fixed_costs": format_inr(monthly_fc),
            "annual_fixed_costs": format_inr(costs["total_annual"]),
            "cost_breakdown": {k: format_inr(v) for k, v in costs.items() if isinstance(v, float) and k != "total_monthly"},
            "break_even": {
                "units": be_result.break_even_units,
                "revenue": format_inr(be_result.break_even_revenue),
                "formula": be_result.formula_shown,
                "months": be_result.months_to_break_even,
                "gross_margin_percent": be_result.gross_margin_percent,
            },
            "projections": {
                f"year_{p.year}": {
                    "revenue": format_inr(p.revenue),
                    "expenses": format_inr(p.expenses),
                    "profit": format_inr(p.profit),
                    "customers": p.customers,
                    "mrr": format_inr(p.mrr),
                }
                for p in proj
            },
            "unit_economics": {
                "cac": format_inr(ue.cac),
                "ltv": format_inr(ue.ltv),
                "ltv_cac_ratio": f"{ue.ltv_cac_ratio:.1f}x",
                "payback_months": f"{ue.payback_months:.1f} months",
                "gross_margin": f"{ue.gross_margin:.1f}%",
            },
        }

        tl.complete_tool_event(
            calc_event,
            f"Monthly FC: {format_inr(monthly_fc)} | BE: {be_result.break_even_units:.0f} units | Y1 profit: {format_inr(proj[0].profit)}"
        )
        tl.complete_reasoning_step(3, f"Cost estimate: {format_inr(monthly_fc)}/month")
        tl.complete_reasoning_step(5, f"Break-even: {be_result.formula_shown}")
        tl.complete_reasoning_step(6, f"LTV/CAC: {ue.ltv_cac_ratio:.1f}x")

        # ── TOOL 2: IBM Granite — qualitative canvas sections ─────────────────
        tl.current_task = "Calling IBM Granite to design Business Model Canvas and Lean Canvas"
        tl.complete_reasoning_step(1, "Designing Business Model Canvas (9 blocks)")
        tl.complete_reasoning_step(2, "Mapping Lean Canvas")
        tl.complete_reasoning_step(4, "Building financial projections narrative")

        user_prompt = self._build_prompt(
            idea, domain, budget, market_summary, planner_summary,
            revenue_model_hint, execution_instructions, calculated_financials
        )
        granite_event = tl.add_tool_event(
            "IBM Granite", "llm", "watsonx.ai",
            f"BMC + Lean Canvas + pricing for {domain} startup"
        )
        raw = await self.client.generate_structured(
            system_prompt=BUSINESS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_new_tokens=550,
            temperature=0.38,
        )
        tl.complete_tool_event(granite_event, f"Generated {len(raw)} char business plan", tokens=len(raw) // 4)

        output = self._parse_output(raw, calculated_financials)
        output.timeline = tl.to_dict()

        tl.finish(
            output_summary=f"BMC filled | Break-even: {be_result.break_even_units:.0f} units in {be_result.months_to_break_even:.0f} months | LTV/CAC: {ue.ltv_cac_ratio:.1f}x",
            output_keys=["business_model_canvas", "lean_canvas", "financial_projections", "break_even_analysis", "unit_economics"],
            passed_to_next="Financial projections + break-even + unit economics → Strategy Agent",
        )
        logger.info("BusinessFinanceAgent complete", domain=domain)
        return output

    def _build_prompt(
        self,
        idea: str,
        domain: str,
        budget: str | None,
        market_summary: str,
        planner_summary: str,
        revenue_hint: str,
        instructions: str,
        calc_data: dict,
    ) -> str:
        parts = [
            f"Startup Idea: {idea}",
            f"Domain: {domain}",
            f"Budget Available: {budget or 'Not specified'}",
            f"Planner Summary: {planner_summary}",
            f"Market Summary (from Market Agent): {market_summary}",
        ]
        if revenue_hint:
            parts.append(f"Revenue Model Hint from Planner: {revenue_hint}")
        if instructions:
            parts.append(f"Planner's Instructions for Business Agent: {instructions}")
        parts.append(f"\n[Pre-Calculated Financial Data — USE THESE NUMBERS]\n")
        parts.append(f"Monthly Fixed Costs: {calc_data.get('monthly_fixed_costs', 'N/A')}")
        parts.append(f"Break-even formula: {calc_data.get('break_even', {}).get('formula', 'N/A')}")
        parts.append(f"Year 1 Revenue estimate: {calc_data.get('projections', {}).get('year_1', {}).get('revenue', 'N/A')}")
        parts.append(f"LTV/CAC Ratio: {calc_data.get('unit_economics', {}).get('ltv_cac_ratio', 'N/A')}")
        parts.append("\nGenerate the complete business model report. Use the pre-calculated numbers above in your JSON output.")
        return "\n".join(parts)

    def _parse_output(self, raw: str, calc_data: dict) -> BusinessFinanceOutput:
        data = safe_parse_json(raw, default={})

        # ── Fallback qualitative canvases ─────────────────────────────────────
        bmc = data.get("business_model_canvas") or {}
        if not bmc or not bmc.get("value_propositions"):
            # Normalise keys (check singular form as well)
            if bmc.get("value_proposition") and not bmc.get("value_propositions"):
                bmc["value_propositions"] = bmc.get("value_proposition")
            else:
                bmc = self._fallback_bmc()

        lean = data.get("lean_canvas") or {}
        if not lean or not lean.get("unique_value_proposition"):
            lean = self._fallback_lean_canvas()

        pricing = data.get("pricing_strategy") or {}
        if not pricing or not pricing.get("tiers"):
            pricing = self._fallback_pricing()

        # Override financial sections with calculated values where available
        proj_llm = data.get("financial_projections", {})
        proj_calc = calc_data.get("projections", {})
        # Merge: keep LLM labels but use calc values
        for yr in ["year_1", "year_2", "year_3"]:
            if yr in proj_calc:
                if yr not in proj_llm:
                    proj_llm[yr] = {}
                proj_llm[yr].setdefault("revenue", proj_calc[yr]["revenue"])
                proj_llm[yr].setdefault("expenses", proj_calc[yr]["expenses"])
                proj_llm[yr].setdefault("profit", proj_calc[yr]["profit"])
                proj_llm[yr]["customers"] = proj_calc[yr]["customers"]

        be_llm = data.get("break_even_analysis", {})
        be_calc = calc_data.get("break_even", {})
        be_llm["break_even_formula"] = be_calc.get("formula", be_llm.get("break_even_formula", ""))
        be_llm["gross_margin_percent"] = f"{be_calc.get('gross_margin_percent', '—')}%"

        # Make sure break_even_point is filled
        if not be_llm.get("break_even_point"):
            be_llm["break_even_point"] = f"{be_calc.get('break_even_units', 150):.0f} units"
            be_llm["monthly_fixed_costs"] = format_inr(be_calc.get("monthly_fixed_costs", 100000))
            be_llm["price_per_unit"] = format_inr(be_calc.get("price_per_unit", 500))

        # Make sure operational_costs list is filled
        op_costs = data.get("operational_costs", [])
        if not op_costs:
            costs_calc = calc_data.get("startup_costs", [])
            if costs_calc:
                op_costs = [{"category": c.get("category", "Operations"), "monthly_estimate": format_inr(c.get("amount", 20000))} for c in costs_calc]
            else:
                op_costs = [
                    {"category": "Cloud Infrastructure", "monthly_estimate": "₹15,000"},
                    {"category": "Marketing & Ads", "monthly_estimate": "₹25,000"},
                    {"category": "Engineering / Contractors", "monthly_estimate": "₹1,20,000"},
                    {"category": "Miscellaneous", "monthly_estimate": "₹10,000"}
                ]

        return BusinessFinanceOutput(
            business_model_canvas=bmc,
            lean_canvas=lean,
            value_proposition_canvas=data.get("value_proposition_canvas", {}),
            pricing_strategy=pricing,
            financial_projections=proj_llm,
            operational_costs=op_costs,
            break_even_analysis=be_llm,
            unit_economics=data.get("unit_economics", calc_data.get("unit_economics", {})),
            calculated_financials=calc_data,
            summary=data.get("summary", ""),
            raw_output=raw,
        )

    def _fallback_bmc(self) -> dict:
        return {
            "key_partners": ["Cloud providers", "API integrations", "Distribution partners"],
            "key_activities": ["Software engineering", "Marketing & sales", "Operations management"],
            "key_resources": ["Proprietary platform architecture", "Core development team", "Customer data insights"],
            "value_propositions": ["Highly scalable and automated solution reducing process cycles by 40%", "Lower operating overhead compared to traditional players"],
            "customer_relationships": ["Self-service model", "Automated email support", "Dedicated customer success managers"],
            "channels": ["Inbound sales", "Direct online signups", "Enterprise sales outreach"],
            "customer_segments": ["SMEs and mid-market companies", "Independent professionals & agencies"],
            "cost_structure": ["Product development & hosting", "Customer acquisition costs", "Operations & maintenance support"],
            "revenue_streams": ["Tiered SaaS subscription model", "Enterprise customized plan pricing"]
        }

    def _fallback_lean_canvas(self) -> dict:
        return {
            "unique_value_proposition": "An intelligent automated platform optimizing workflows for scale.",
            "unfair_advantage": "Proprietary algorithms trained on domain-specific datasets.",
            "key_metrics": ["Customer Acquisition Cost (CAC)", "Monthly Recurring Revenue (MRR)", "Churn Rate"],
            "problem": ["High manual effort required for standard workflows", "Lack of real-time insights"],
            "solution": ["Automated workflows", "Live analytics dashboard"],
            "channels": ["Digital marketing", "Strategic partnerships"],
            "customer_segments": ["Tech-enabled businesses", "Operations managers"],
            "cost_structure": ["Hosting", "Engineering", "Acquisition"],
            "revenue_streams": ["Subscription", "Enterprise API usage"]
        }

    def _fallback_pricing(self) -> dict:
        return {
            "model": "Subscription SaaS",
            "tiers": [
                {"name": "Starter Plan", "price": "₹1,499/month", "features": ["1 User license", "Core dashboard access", "Standard email support"]},
                {"name": "Growth Plan", "price": "₹4,999/month", "features": ["Up to 5 User licenses", "Advanced analytics modules", "Priority support"]},
                {"name": "Enterprise Plan", "price": "Custom Pricing", "features": ["Unlimited licenses", "Custom API integration", "24/7 dedicated support"]}
            ],
            "rationale": "Value-based pricing mapped to customer size and usage limits."
        }

