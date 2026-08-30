"""API routers."""
from app.api.auth import router as auth_router
from app.api.auth_extra import router as auth_extra_router
from app.api.projects import router as projects_router
from app.api.vendors import router as vendors_router
from app.api.project_vendors import router as project_vendors_router
from app.api.requirements import router as requirements_router
from app.api.proposals import router as proposals_router
from app.api.proposals_detail import router as proposals_detail_router
from app.api.proposals_actions import router as proposals_actions_router
from app.api.analysis import router as analysis_router
from app.api.comparison import router as comparison_router
from app.api.recommendations import router as recommendations_router
from app.api.copilot import router as copilot_router
from app.api.reports import router as reports_router
from app.api.audit import router as audit_router
from app.api.dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "auth_extra_router",
    "projects_router",
    "vendors_router",
    "project_vendors_router",
    "requirements_router",
    "proposals_router",
    "proposals_detail_router",
    "proposals_actions_router",
    "analysis_router",
    "comparison_router",
    "recommendations_router",
    "copilot_router",
    "reports_router",
    "audit_router",
    "dashboard_router",
]
