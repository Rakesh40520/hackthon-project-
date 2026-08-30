"""FastAPI application entrypoint."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import (
    analysis_router,
    audit_router,
    auth_extra_router,
    auth_router,
    comparison_router,
    copilot_router,
    dashboard_router,
    project_vendors_router,
    projects_router,
    proposals_actions_router,
    proposals_detail_router,
    proposals_router,
    recommendations_router,
    reports_router,
    requirements_router,
    vendors_router,
)
from app.config import settings
from app.database import engine
from app.schemas.common import HealthResponse

logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered procurement intelligence platform.\n\n"
        "Upload vendor proposals, extract structured data with pluggable AI providers, "
        "evaluate requirements, detect risks, normalize pricing, score vendors objectively, "
        "and produce explainable recommendations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = settings.API_PREFIX
app.include_router(auth_router, prefix=PREFIX)
app.include_router(auth_extra_router, prefix=PREFIX)
app.include_router(projects_router, prefix=PREFIX)
app.include_router(vendors_router, prefix=PREFIX)
app.include_router(project_vendors_router, prefix=PREFIX)
app.include_router(requirements_router, prefix=PREFIX)
app.include_router(proposals_router, prefix=PREFIX)
app.include_router(proposals_detail_router, prefix=PREFIX)
app.include_router(proposals_actions_router, prefix=PREFIX)
app.include_router(analysis_router, prefix=PREFIX)
app.include_router(comparison_router, prefix=PREFIX)
app.include_router(recommendations_router, prefix=PREFIX)
app.include_router(copilot_router, prefix=PREFIX)
app.include_router(reports_router, prefix=PREFIX)
app.include_router(audit_router, prefix=PREFIX)
app.include_router(dashboard_router, prefix=PREFIX)


@app.get("/", tags=["Health"])
async def root() -> dict:
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    db_ok = True
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.warning("DB health check failed: %s", e)
        db_ok = False
    return HealthResponse(
        status=("ok" if db_ok else "degraded"),
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors()), "body": exc.body if isinstance(exc.body, (dict, list, str, int, float, bool, type(None))) else str(exc.body)},
    )