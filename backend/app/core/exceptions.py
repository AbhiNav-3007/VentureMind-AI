"""
VentureMind AI — Custom Exception Hierarchy
"""

from fastapi import HTTPException, status


class VentureMindException(Exception):
    """Base exception for all VentureMind errors."""
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AgentExecutionError(VentureMindException):
    """Raised when an AI agent fails during execution."""


class OrchestratorError(VentureMindException):
    """Raised when the orchestrator workflow fails."""


class IBMServiceError(VentureMindException):
    """Raised when an IBM Cloud service call fails."""


class RAGError(VentureMindException):
    """Raised when the RAG pipeline fails."""


class ReportGenerationError(VentureMindException):
    """Raised when PDF/report generation fails."""


class DatabaseError(VentureMindException):
    """Raised when a database operation fails."""


class BlueprintNotFoundError(VentureMindException):
    """Raised when a requested blueprint does not exist."""


# ── HTTP Exception helpers ────────────────────────────────────────────────────

def raise_not_found(resource: str) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found.")


def raise_bad_request(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def raise_internal_error(detail: str = "Internal server error.") -> None:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
