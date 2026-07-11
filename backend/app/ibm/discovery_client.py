"""
VentureMind AI — Watson Discovery stub (disabled)
==================================================
IBM Watson Discovery has no free/Lite tier. This module provides a
no-op stub so all imports resolve and the agents degrade gracefully
to RAG-only mode without crashing.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class WatsonDiscoveryClient:
    """
    Disabled stub — Watson Discovery is not available on the Lite plan.
    All query() calls return an empty list immediately so agents fall back
    to the local RAG knowledge base (ChromaDB) automatically.
    """

    async def query(
        self,
        natural_language_query: str,  # noqa: ARG002
        count: int = 5,               # noqa: ARG002
        fields: list[str] | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Returns empty list — Discovery is disabled (no Lite plan available)."""
        logger.debug("Watson Discovery is disabled; returning empty results")
        return []


@lru_cache(maxsize=1)
def get_discovery_client() -> WatsonDiscoveryClient:
    """Return the singleton (disabled) Discovery stub."""
    return WatsonDiscoveryClient()
