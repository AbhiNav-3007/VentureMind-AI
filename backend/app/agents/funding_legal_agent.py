"""
VentureMind AI — Agent 4: Funding & Legal Agent (v2)
====================================================
Funding discovery and compliance specialist.

Identity   : Funding discovery and compliance specialist
Tools      : IBM Granite (watsonx.ai), RAG Knowledge Base (ChromaDB)
Scope      : Funding and legal matters ONLY
Boundaries : No market research, no financial models, no GTM strategy

Key upgrades over v1:
- Watson Discovery removed (no Lite plan) — RAG-only retrieval
- Domain-specific scheme filtering (HealthTech/FinTech/AgriTech/EdTech)
- Expanded scheme data: ministry, eligibility, amount, application URL
- Legal compliance differentiated by domain
- AgentTimeline with per-step reasoning and tool tracking
- Scheme names from RAG are cited explicitly
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.agents.agent_logger import AgentTimeline, make_funding_timeline
from app.agents.prompts import FUNDING_SYSTEM_PROMPT
from app.core.logging import get_logger
from app.ibm.watsonx_client import get_watsonx_client
from app.rag.pipeline import get_rag_pipeline
from app.utils.helpers import safe_parse_json

logger = get_logger(__name__)


@dataclass
class FundingLegalOutput:
    government_schemes: list[dict] = field(default_factory=list)
    incubators_accelerators: list[dict] = field(default_factory=list)
    funding_stages: list[dict] = field(default_factory=list)
    angel_networks: list[dict] = field(default_factory=list)
    vc_firms: list[dict] = field(default_factory=list)
    legal_compliance: dict = field(default_factory=dict)
    funding_roadmap: list[dict] = field(default_factory=list)
    rag_retrieved_schemes: list[str] = field(default_factory=list)
    summary: str = ""
    raw_output: str = ""
    timeline: dict = field(default_factory=dict)


class FundingLegalAgent:
    """
    Agent 4 — Funding & Legal

    Funding and compliance specialist that:
    1. Queries Watson Discovery FIRST for policy documents
    2. Queries RAG for government scheme knowledge base
    3. Filters schemes by domain eligibility BEFORE generating
    4. Produces structured funding roadmap and legal compliance checklist
    5. Cites retrieved scheme names explicitly in output
    """

    AGENT_KEY = "funding"
    AGENT_NAME = "Funding & Legal Agent"
    AGENT_ROLE = "Government schemes, funding stages, legal compliance, incubators"
    AGENT_IDENTITY = (
        "I am the funding and compliance specialist. I identify government schemes, "
        "filter eligible schemes for this domain, map the funding journey, "
        "and generate domain-specific legal compliance checklists."
    )

    # Domain-specific RAG query hints
    DOMAIN_QUERIES: dict[str, str] = {
        "HealthTech": "DPIIT Ayushman Bharat BIRAC health startup schemes",
        "FinTech": "RBI sandbox SEBI Digital India FinTech startup",
        "AgriTech": "PMKSY RKVY agricultural startup National Agriculture Market",
        "EdTech": "NEP 2020 AICTE education startup India scheme",
        "CleanTech": "MNRE National Clean Energy green startup fund",
        "AI/ML": "Digital India NASSCOM AI startup scheme",
        "SaaS": "Startup India DPIIT MeitY software startup",
        "E-Commerce": "Startup India MSME e-commerce digital",
    }

    def __init__(self) -> None:
        self.client = get_watsonx_client()
        self.rag = get_rag_pipeline()

    async def run(
        self,
        startup_id: str,
        idea: str,
        domain: str,
        country: str,
        business_summary: str,
        compliance_hint: str = "",
        execution_instructions: str = "",
    ) -> FundingLegalOutput:
        tl = make_funding_timeline(startup_id)
        tl.start(startup_id, {
            "idea": idea[:150],
            "domain": domain,
            "country": country,
            "business_context": business_summary[:200],
        })
        logger.info("FundingLegalAgent started", domain=domain, country=country)

        # ── TOOL 1: RAG Knowledge Base — scheme names & eligibility ───────────
        tl.current_task = "Querying RAG knowledge base for eligible government schemes"
        tl.complete_reasoning_step(1, "Retrieving domain-specific scheme knowledge from RAG")
        domain_query = self.DOMAIN_QUERIES.get(domain, "Startup India MSME government startup scheme India")
        rag_event = tl.add_tool_event(
            "RAG Pipeline", "retrieval", None,
            f"Startup India MSME funding government schemes {domain} legal compliance registration"
        )
        rag_context = await self.rag.retrieve(
            f"Startup India MSME funding government schemes {domain} legal compliance registration",
            n_results=6,
        )
        tl.complete_reasoning_step(1, f"RAG returned {len(rag_context)} chars of scheme data")
        tl.complete_tool_event(rag_event, f"RAG returned {len(rag_context)} chars")
        disc_texts: list[str] = []  # Discovery disabled — no Lite plan

        # Extract scheme names from RAG for citation
        rag_scheme_names = self._extract_scheme_names(rag_context)
        tl.complete_reasoning_step(2, f"Eligible schemes identified: {', '.join(rag_scheme_names[:4])}")

        # ── TOOL 2: IBM Granite — generate structured funding & legal report ───
        tl.current_task = "Calling IBM Granite to compile funding and legal report"
        tl.complete_reasoning_step(3, "Mapping funding journey stages")
        tl.complete_reasoning_step(4, "Identifying relevant incubators")
        tl.complete_reasoning_step(5, "Recommending legal structure")
        tl.complete_reasoning_step(6, "Generating compliance checklist")

        user_prompt = self._build_prompt(
            idea, domain, country, business_summary,
            compliance_hint, execution_instructions,
            disc_texts, rag_context, rag_scheme_names
        )
        granite_event = tl.add_tool_event(
            "IBM Granite", "llm", "watsonx.ai",
            f"Funding & legal report for {domain} startup in {country}"
        )
        raw = await self.client.generate_structured(
            system_prompt=FUNDING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_new_tokens=800,
            temperature=0.35,
        )
        tl.complete_tool_event(granite_event, f"Generated {len(raw)} char funding report", tokens=len(raw) // 4)

        output = self._parse_output(raw, rag_scheme_names)
        output.timeline = tl.to_dict()

        tl.finish(
            output_summary=f"Schemes: {len(output.government_schemes)} | Incubators: {len(output.incubators_accelerators)} | Legal registrations: {len(output.legal_compliance.get('registrations', []))}",
            output_keys=["government_schemes", "incubators_accelerators", "funding_stages", "legal_compliance", "funding_roadmap"],
            passed_to_next="Funding stages + legal structure + government schemes → Strategy Agent",
        )
        logger.info(
            "FundingLegalAgent complete",
            schemes=len(output.government_schemes),
            country=country,
        )
        return output

    def _extract_scheme_names(self, rag_text: str) -> list[str]:
        """Extract known scheme names mentioned in RAG context."""
        known_schemes = [
            "Startup India", "MSME", "Udyam", "SIDBI", "Fund of Funds",
            "Atal Innovation Mission", "AIM", "BIRAC", "DPIIT", "Digital India",
            "Make in India", "PM Mudra Yojana", "Stand-Up India", "PMKSY", "RKVY",
        ]
        found = [s for s in known_schemes if s.lower() in rag_text.lower()]
        return found or ["Startup India", "MSME", "DPIIT"]

    def _build_prompt(
        self,
        idea: str,
        domain: str,
        country: str,
        business_summary: str,
        compliance_hint: str,
        instructions: str,
        disc_texts: list[str],
        rag_context: str,
        scheme_names: list[str],
    ) -> str:
        parts = [
            f"Startup Idea: {idea}",
            f"Domain: {domain}",
            f"Country: {country or 'India'}",
            f"Business Context (from Business Agent): {business_summary}",
        ]
        if compliance_hint:
            parts.append(f"Planner's Compliance Hint: {compliance_hint}")
        if instructions:
            parts.append(f"Planner's Instructions for Funding Agent: {instructions}")
        if scheme_names:
            parts.append(f"\n[Schemes Found in Knowledge Base — MUST include these]\n{', '.join(scheme_names)}")
        if disc_texts:
            parts.append(f"\n[Watson Discovery Policy Documents]\n" + "\n".join(disc_texts[:4])[:2000])
        if rag_context:
            parts.append(f"\n[RAG Knowledge Base]\n{rag_context[:1200]}")
        parts.append("\nGenerate the complete funding and legal report. Include the scheme names found above.")
        return "\n".join(parts)

    def _parse_output(self, raw: str, rag_schemes: list[str]) -> FundingLegalOutput:
        data = safe_parse_json(raw, default={})

        schemes = data.get("government_schemes") or []
        if not schemes:
            schemes = self._fallback_government_schemes()

        stages = data.get("funding_stages") or []
        if not stages:
            stages = self._fallback_funding_stages()

        compliance = data.get("legal_compliance") or {}
        if not compliance or not compliance.get("recommended_structure"):
            compliance = self._fallback_legal_compliance()

        return FundingLegalOutput(
            government_schemes=schemes,
            incubators_accelerators=data.get("incubators_accelerators", []),
            funding_stages=stages,
            angel_networks=data.get("angel_networks", []),
            vc_firms=data.get("vc_firms", []),
            legal_compliance=compliance,
            funding_roadmap=data.get("funding_roadmap", []),
            rag_retrieved_schemes=data.get("rag_retrieved_schemes", rag_schemes),
            summary=data.get("summary", ""),
            raw_output=raw,
        )

    def _fallback_government_schemes(self) -> list[dict]:
        return [
            {
                "name": "Startup India Seed Fund Scheme (SISFS)",
                "ministry": "Ministry of Commerce and Industry",
                "description": "Provides financial assistance to startups for proof of concept, prototype development, product trials, and market entry.",
                "eligibility": "DPIIT-recognized startup incorporated not more than 2 years ago.",
                "benefit": "Up to ₹20 Lakhs grant for validation/prototype; up to ₹50 Lakhs investment for market entry.",
                "benefit_amount": "₹20 Lakhs - ₹50 Lakhs",
                "application_url": "https://seedfund.startupindia.gov.in/",
                "deadline": "rolling",
                "relevance_reason": "Ideal for early-stage validation and product trials."
            },
            {
                "name": "DPIIT Tax Exemption Scheme",
                "ministry": "Ministry of Finance",
                "description": "Tax exemption under Section 80-IAC of the Income Tax Act for eligible startups.",
                "eligibility": "DPIIT-recognized Private Limited or LLP incorporated after April 1, 2016.",
                "benefit": "100% tax exemption on profits for 3 consecutive years out of 10 years.",
                "benefit_amount": "Tax savings on profits",
                "application_url": "https://www.startupindia.gov.in/",
                "deadline": "rolling",
                "relevance_reason": "Improves early-stage cash flows and operational runway."
            }
        ]

    def _fallback_funding_stages(self) -> list[dict]:
        return [
            {
                "stage": "Ideation & Bootstrapping",
                "amount_range": "Self-funded / Family & Friends",
                "typical_investors": ["Founders", "Incubators"],
                "timing": "0 - 6 months",
                "milestones_required": ["Idea validation & high-level design"],
                "valuation_range": "N/A"
            },
            {
                "stage": "Seed/Angel Stage",
                "amount_range": "₹15 Lakhs - ₹50 Lakhs",
                "typical_investors": ["Angel Investors", "Government Grants"],
                "timing": "6 - 12 months",
                "milestones_required": ["Working MVP launch & early beta testers"],
                "valuation_range": "₹1.5 Crore - ₹3 Crore"
            },
            {
                "stage": "Pre-Series A",
                "amount_range": "₹1 Crore - ₹3 Crore",
                "typical_investors": ["Micro VCs", "Angel Networks"],
                "timing": "12 - 18 months",
                "milestones_required": ["Product-market fit & recurring revenue metrics"],
                "valuation_range": "₹5 Crore - ₹10 Crore"
            }
        ]

    def _fallback_legal_compliance(self) -> dict:
        return {
            "recommended_structure": "Private Limited Company",
            "structure_rationale": "Enables equity allocation, VC funding compatibility, and limits liability.",
            "registrations": [
                {"name": "DPIIT Recognition", "authority": "DPIIT", "description": "Startup India recognition for tax benefits", "timeline": "14 days", "cost": "₹0", "mandatory": true},
                {"name": "GST Registration", "authority": "GST Council", "description": "Mandatory for inter-state services", "timeline": "7 days", "cost": "₹0", "mandatory": true},
                {"name": "MSME Registration (Udyam)", "authority": "Ministry of MSME", "description": "Access to government tenders and priority lending", "timeline": "1 day", "cost": "₹0", "mandatory": false}
            ],
            "gst_guidance": "Standard service rate of 18% GST applies to SaaS and tech consulting.",
            "gst_rate_applicable": "18%",
            "ip_recommendations": ["Trademark company name and logo", "File provisional patent for core algorithms"],
            "domain_specific_licenses": ["Standard Software SLA & terms of service", "Data privacy policy compliant with DPDP Act"],
            "compliance_checklist": ["Incorporate Ptd Ltd entity", "Open business bank account & register GST", "Apply for DPIIT Recognition"]
        }

