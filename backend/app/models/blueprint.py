"""
VentureMind AI — ORM model: Startup Blueprint
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Blueprint(Base):
    """Stores the fully generated startup blueprint for each idea."""

    __tablename__ = "blueprints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    startup_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("startup_ideas.id", ondelete="CASCADE"), nullable=False
    )

    # Structured JSON sections
    executive_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    market_research: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    competitor_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    swot_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    customer_personas: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    business_model: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    lean_canvas: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    financial_plan: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    funding_opportunities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    legal_compliance: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    marketing_strategy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    product_roadmap: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    risk_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    investor_pitch: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    final_recommendations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # PDF storage
    pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_cos_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    startup: Mapped["StartupIdea"] = relationship("StartupIdea", back_populates="blueprint")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Blueprint id={self.id} startup_id={self.startup_id}>"
