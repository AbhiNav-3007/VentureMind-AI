"""
VentureMind AI — RAG Knowledge Base Seeder
Run once to ingest startup / funding / legal documents into ChromaDB.
"""

from __future__ import annotations

import asyncio
import uuid

from app.rag.pipeline import get_rag_pipeline

# Seed data: startup policy, Startup India, MSME, legal basics
SEED_DOCUMENTS = [
    {
        "id": str(uuid.uuid4()),
        "text": (
            "Startup India is a flagship initiative of the Government of India launched in 2016. "
            "It provides tax exemptions for 3 years, funding through SIDBI Fund of Funds, "
            "fast-track patent examination, and self-certification under labour laws. "
            "Eligible startups must be incorporated as Private Limited Company, LLP, or Partnership firm "
            "and should have an annual turnover not exceeding ₹100 crore."
        ),
        "metadata": {"source": "Startup India", "category": "government_scheme"},
    },
    {
        "id": str(uuid.uuid4()),
        "text": (
            "MSME (Micro, Small & Medium Enterprises) classification in India: "
            "Micro enterprises have investment up to ₹1 crore and turnover up to ₹5 crore. "
            "Small enterprises: investment up to ₹10 crore, turnover up to ₹50 crore. "
            "Medium enterprises: investment up to ₹50 crore, turnover up to ₹250 crore. "
            "MSME registration (Udyam) provides access to priority sector lending, government tenders, "
            "and credit guarantee schemes."
        ),
        "metadata": {"source": "MSME", "category": "government_scheme"},
    },
    {
        "id": str(uuid.uuid4()),
        "text": (
            "Legal structures for Indian startups: "
            "1. Private Limited Company (Pvt Ltd) — most popular for VC funding, limited liability, easy share transfer. "
            "2. Limited Liability Partnership (LLP) — fewer compliances, suitable for small teams. "
            "3. One Person Company (OPC) — for solo founders. "
            "Key registrations: Certificate of Incorporation, PAN, TAN, GST, Shop Act, "
            "FSSAI (food), DPIIT recognition for startup benefits."
        ),
        "metadata": {"source": "MCA India", "category": "legal"},
    },
    {
        "id": str(uuid.uuid4()),
        "text": (
            "Pre-seed funding in India: typically ₹10–50 lakhs from founders, family & friends, or angel investors. "
            "Seed round: ₹50 lakhs – ₹5 crore from angel networks like Indian Angel Network (IAN), "
            "Mumbai Angels, Lead Angels, or early-stage VCs. "
            "Series A: ₹5–50 crore from venture capital firms like Sequoia Capital India, "
            "Accel Partners, Blume Ventures, Nexus Venture Partners."
        ),
        "metadata": {"source": "IVCA", "category": "funding"},
    },
    {
        "id": str(uuid.uuid4()),
        "text": (
            "Top Indian startup incubators and accelerators: "
            "1. IIT Bombay (SINE) — deep tech focus. "
            "2. IIM Ahmedabad (CIIE) — business innovation. "
            "3. T-Hub Hyderabad — largest in Asia. "
            "4. NASSCOM 10,000 Startups — IT/tech sector. "
            "5. Atal Innovation Mission (AIM) — government-backed, nationwide. "
            "6. YCombinator (global) — top accelerator with India portfolio."
        ),
        "metadata": {"source": "AIM India", "category": "incubator"},
    },
    {
        "id": str(uuid.uuid4()),
        "text": (
            "Go-to-market strategy frameworks for B2B SaaS startups: "
            "Product-led growth (PLG) uses free tiers to acquire users organically. "
            "Sales-led growth targets enterprise accounts with direct outreach. "
            "Channel partnerships leverage resellers and system integrators. "
            "Key GTM metrics: CAC (Customer Acquisition Cost), LTV (Lifetime Value), "
            "churn rate, NPS, MRR (Monthly Recurring Revenue)."
        ),
        "metadata": {"source": "GTM Strategy Guide", "category": "strategy"},
    },
    {
        "id": str(uuid.uuid4()),
        "text": (
            "Business Model Canvas has 9 building blocks: "
            "1. Key Partners, 2. Key Activities, 3. Key Resources, "
            "4. Value Propositions, 5. Customer Relationships, 6. Channels, "
            "7. Customer Segments, 8. Cost Structure, 9. Revenue Streams. "
            "Common revenue models for startups: SaaS subscription, marketplace commission, "
            "freemium, pay-per-use, transaction fee, licensing."
        ),
        "metadata": {"source": "Business Model Generation", "category": "business_model"},
    },
    {
        "id": str(uuid.uuid4()),
        "text": (
            "GST registration in India is mandatory for businesses with annual turnover above ₹20 lakhs "
            "(₹10 lakhs for special category states). "
            "Startups providing digital services or e-commerce must register regardless of turnover. "
            "GST rates: 0%, 5%, 12%, 18%, 28%. Most software services attract 18% GST. "
            "Input Tax Credit (ITC) allows businesses to offset GST paid on inputs."
        ),
        "metadata": {"source": "GST India", "category": "legal"},
    },
]


async def seed_knowledge_base() -> None:
    """Ingest seed documents into ChromaDB."""
    pipeline = get_rag_pipeline()
    pipeline.ingest_documents(SEED_DOCUMENTS)
    print(f"✅ Seeded {len(SEED_DOCUMENTS)} documents into ChromaDB.")


if __name__ == "__main__":
    asyncio.run(seed_knowledge_base())
