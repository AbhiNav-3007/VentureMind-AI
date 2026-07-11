"""
VentureMind AI — RAG Pipeline (ChromaDB-only)
=============================================
Uses ChromaDB for local vector search.
Watson Discovery has been removed (no free/Lite plan available).
"""

from __future__ import annotations

from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.core.exceptions import RAGError
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline using ChromaDB local embeddings.

    Watson Discovery was removed — no Lite plan is available.
    The pipeline gracefully returns an empty string if ChromaDB is not running,
    so agents fall back to pure Granite generation.
    """

    def __init__(self) -> None:
        self._chroma: chromadb.HttpClient | None = None

    @property
    def chroma(self) -> chromadb.HttpClient:
        if self._chroma is None:
            self._chroma = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._chroma

    def _get_collection(self) -> chromadb.Collection:
        return self.chroma.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Ingest ────────────────────────────────────────────────────────────────

    def ingest_documents(self, documents: list[dict]) -> None:
        """
        Store documents in ChromaDB for local vector search.

        Args:
            documents: List of {"id": str, "text": str, "metadata": dict}
        """
        collection = self._get_collection()
        try:
            collection.add(
                ids=[d["id"] for d in documents],
                documents=[d["text"] for d in documents],
                metadatas=[d.get("metadata", {}) for d in documents],
            )
            logger.info("RAG ingest complete", count=len(documents))
        except Exception as exc:
            raise RAGError("ChromaDB ingest failed", {"error": str(exc)}) from exc

    # ── Retrieve ──────────────────────────────────────────────────────────────

    async def retrieve(
        self,
        query: str,
        n_results: int = 5,
        use_discovery: bool = False,  # kept for call-site compatibility; always ignored
    ) -> str:
        """
        Retrieve relevant passages from ChromaDB.

        Returns:
            A formatted string of passages to inject into a Granite prompt,
            or an empty string if ChromaDB is unavailable.
        """
        passages: list[str] = []

        try:
            collection = self._get_collection()
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents"],
            )
            for doc in results.get("documents", [[]])[0]:
                passages.append(f"[Knowledge Base] {doc}")
        except Exception as exc:
            logger.warning("ChromaDB retrieval skipped (not running?)", error=str(exc))

        if not passages:
            return ""

        context = "\n\n".join(passages[:n_results])
        logger.info("RAG context assembled", chars=len(context))
        return context


_rag_pipeline: RAGPipeline | None = None


def get_rag_pipeline() -> RAGPipeline:
    """Return a singleton RAG pipeline."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
