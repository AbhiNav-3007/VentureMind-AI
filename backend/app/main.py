"""
VentureMind AI — FastAPI Application Entry Point
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import export, startups, timelines, websocket
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.session import create_all_tables

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    configure_logging(debug=settings.DEBUG)
    logger.info("VentureMind AI starting up", version=settings.APP_VERSION)
    await create_all_tables()
    logger.info("Database tables verified / created")
    yield
    logger.info("VentureMind AI shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Autonomous Startup Incubator — 5 AI Agents powered by IBM Granite (watsonx.ai) "
            "that transform a raw startup idea into a complete investor-ready blueprint."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(startups.router, prefix=settings.API_PREFIX)
    app.include_router(export.router, prefix=settings.API_PREFIX)
    app.include_router(timelines.router, prefix=settings.API_PREFIX)
    app.include_router(websocket.router, prefix=settings.API_PREFIX)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "service": settings.APP_NAME})

    return app


app = create_app()
