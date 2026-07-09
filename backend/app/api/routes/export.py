"""
VentureMind AI — PDF Export API Route
GET /api/v1/export/{startup_id}/pdf  → generate and return PDF
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import raise_not_found
from app.core.logging import get_logger
from app.db.session import get_db
from app.ibm.cos_client import get_cos_client
from app.models.blueprint import Blueprint
from app.models.startup import StartupIdea
from app.report.pdf_generator import generate_pdf_report

logger = get_logger(__name__)
router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/{startup_id}/pdf")
async def export_pdf(
    startup_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Generate and stream a PDF report for a completed blueprint.
    Also uploads the PDF to IBM COS and stores the URL.
    """
    # Load startup idea
    startup_result = await db.execute(
        select(StartupIdea).where(StartupIdea.id == uuid.UUID(startup_id))
    )
    startup = startup_result.scalar_one_or_none()
    if not startup:
        raise_not_found("Startup idea")

    # Load blueprint
    bp_result = await db.execute(
        select(Blueprint).where(Blueprint.startup_id == uuid.UUID(startup_id))
    )
    blueprint = bp_result.scalar_one_or_none()
    if not blueprint:
        raise_not_found("Blueprint — generation may still be in progress")

    # Generate PDF
    pdf_bytes = await generate_pdf_report(startup=startup, blueprint=blueprint)

    # Upload to IBM COS
    try:
        cos = get_cos_client()
        cos_key = f"reports/{startup_id}/blueprint.pdf"
        pdf_url = cos.upload_bytes(key=cos_key, data=pdf_bytes)
        blueprint.pdf_url = pdf_url
        blueprint.pdf_cos_key = cos_key
        await db.commit()
        logger.info("PDF uploaded to COS", key=cos_key)
    except Exception as exc:
        logger.warning("COS upload failed, returning bytes directly", error=str(exc))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="venturemind_blueprint_{startup_id[:8]}.pdf"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.get("/{startup_id}/pdf-url")
async def get_pdf_url(
    startup_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return the IBM COS pre-signed URL for an already-generated PDF."""
    bp_result = await db.execute(
        select(Blueprint).where(Blueprint.startup_id == uuid.UUID(startup_id))
    )
    blueprint = bp_result.scalar_one_or_none()
    if not blueprint:
        raise_not_found("Blueprint")
    if not blueprint.pdf_cos_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not yet generated. Call /export/{startup_id}/pdf first.",
        )
    cos = get_cos_client()
    url = cos.generate_presigned_url(blueprint.pdf_cos_key, expiration=3600)
    return {"pdf_url": url, "expires_in_seconds": 3600}
