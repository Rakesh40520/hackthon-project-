"""Quick smoke test: import all major modules and print summary."""
import sys
sys.path.insert(0, "backend")
print("[1/6] Importing app.config...", flush=True)
from app.config import settings
print(f"      OK - {settings.APP_NAME} v{settings.APP_VERSION}")

print("[2/6] Importing models...", flush=True)
from app import models
print(f"      OK - {len([a for a in dir(models) if not a.startswith('_')])} exports")

print("[3/6] Importing AI module...", flush=True)
from app.ai import get_ai_provider
ai = get_ai_provider()
print(f"      OK - provider: {ai.name}")

print("[4/6] Importing security...", flush=True)
from app.security import hash_password, verify_password
h = hash_password("test123")
assert verify_password("test123", h)
print(f"      OK - password hash roundtrip")

print("[5/6] Importing schemas...", flush=True)
from app.schemas.auth import UserCreate, UserLogin, TokenResponse
from app.schemas.project import ProjectCreate, RequirementCreate
from app.schemas.proposal import ProposalCreate, ProposalDetailOut
from app.schemas.analysis import VendorScoreOut, PricingDetailOut
from app.schemas.copilot import ComparisonOut, CopilotChatRequest
print(f"      OK - all Pydantic schemas")

print("[6/6] Importing services...", flush=True)
from app.services.audit_service import record_audit
from app.services.job_service import get_or_create_job
from app.services.extraction_service import run_extraction
from app.services.evaluation_steps import evaluate_requirements
from app.services.risk_steps import analyze_risks
from app.services.scoring_service import compute_vendor_score
from app.services.scoring_subs import _score_price
from app.services.scoring_subs2 import _score_support
from app.services.analysis_orchestrator import run_full_analysis
from app.services.report_service import generate_pdf_report, generate_xlsx_report
print(f"      OK - all services")

print("\nALL IMPORTS OK", flush=True)
