"""
VentureMind AI — ORM model: Startup Idea
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class StartupIdea(Base):
    """Stores every startup blueprint request submitted by the user."""

    __tablename__ = "startup_ideas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    idea_text: Mapped[str] = mapped_column(Text, nullable=False)
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target_audience: Mapped[str | None] = mapped_column(String(500), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True, default="India")
    budget: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending | running | done | failed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    blueprint: Mapped["Blueprint"] = relationship("Blueprint", back_populates="startup", uselist=False)  # noqa: F821
    agent_logs: Mapped[list["AgentLog"]] = relationship("AgentLog", back_populates="startup")  # noqa: F821

    def __repr__(self) -> str:
        return f"<StartupIdea id={self.id} status={self.status}>"
