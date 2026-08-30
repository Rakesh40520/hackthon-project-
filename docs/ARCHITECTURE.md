# Architecture

## System overview

```
┌───────────────┐                              ┌────────────────────────────────────┐
│  React SPA    │   REST/JSON (JWT)            │ FastAPI                            │
│  Vite + Tail  │ ───────────────────────────▶ │  app/api (routers)                  │
│  TanStack Q   │                              │  app/services (business logic)     │
│  Recharts     │                              │  app/ai (pluggable LLM providers)  │
│  Lucide       │                              │  app/document_processing           │
└───────┬───────┘                              │  app/security (JWT, RBAC)          │
        │                                      │  app/repositories                  │
        │ uploads (multipart)                  └──┬─────────────┬─────────────┬──────┘
        ▼                                         │             │             │
┌───────────────┐                                 ▼             ▼             ▼
│  Local FS     │   ◀─── /uploads/projects/<pid>/<vid>/file.pdf
└───────────────┘                            ┌─────────┐  ┌──────────┐  ┌──────────┐
                                             │ Postgres│  │  Redis   │  │  Celery  │
                                             │ (truth) │  │ (cache + │  │ (worker) │
                                             │         │  │ broker)  │  │          │
                                             └─────────┘  └──────────┘  └──────────┘
```

## Analysis pipeline

```
Upload proposal (multipart)
        │
        ▼
Create Proposal (status=QUEUED) + AnalysisJob (status=PENDING)
        │
        ▼
Background task ─────▶ 1. Extract (PyMuPDF / python-docx / openpyxl)
        │              2. Vendor info  (structured Pydantic)
        │              3. Pricing      (normalize to year1/year3/year5)
        │              4. Technical    (boolean capabilities)
        │              5. Requirements (per-requirement evaluation)
        │              6. Risks        (commercial/technical/security/contract)
        │              7. Missing info
        │              8. Clarifications
        │              9. Deterministic weighted scoring
        │             10. Recommendation (LLM explains objective score)
        │
        ▼
Proposal.status = COMPLETED, Job.status = COMPLETED (progress=100)
```

Each step is idempotent and can be re-run.

## AI provider abstraction

```
app/ai/provider.py
        ▲
        │  AIProvider
        │  ├── complete(messages, response_model, ...) -> Pydantic model
        │  ├── chat(messages, ...) -> str
        │  └── embed(text) -> list[float]
        │
   ┌────┴─────────────────────────────────────┐
   │                                          │
mock_provider      openai_provider     anthropic_provider     gemini_provider     ollama_provider
(no API key)       (gpt-4o-mini)       (claude-3-5-sonnet)    (gemini-1.5-flash)   (local llama)
```

All providers are accessed via `app.ai.factory.get_ai_provider()` which caches a
singleton based on `AI_PROVIDER` setting. The mock provider uses deterministic
regex/keyword heuristics on the proposal text — it **never fabricates** features
and returns `null`/`UNKNOWN` when nothing is found.

## Storage abstraction

```python
class LocalStorage:
    def save(project_id, vendor_id, filename, source) -> (path, size)
    def open(path)
    def delete(path)
    def exists(path)
```

The interface is the same as you'd implement for S3 / R2 / MinIO. Files live
under `/uploads/projects/<project_id>/<vendor_id>/<uuid>_<filename>` and are
never exposed via static URLs.

## Authentication

- `POST /api/auth/register`  → user + access + refresh tokens
- `POST /api/auth/login`     → user + access + refresh tokens
- `POST /api/auth/refresh`   → new access token (refresh hashed in DB)
- `POST /api/auth/logout`    → revoke refresh token
- `GET  /api/auth/me`        → current user

Tokens carry `sub`, `role`, and `email`; RBAC is enforced via the
`require_roles(...)` dependency.

## Database design notes

- All primary keys are UUIDs.
- Money fields use `Numeric(18, 2)` to avoid float drift.
- JSONB used for assumptions, raw breakdowns, audit metadata, recommendation
  strengths/weaknesses/next_steps.
- Enums are defined both in SQLAlchemy (`Enum(...)`) and Pydantic.
- Indexes on commonly filtered columns (project_id, vendor_id, status).

## Frontend state

- **TanStack Query** owns all server state (caching, polling, invalidation).
- **React Router** for routes; protected routes are wrapped in `<Protected>`.
- **AuthProvider** holds the current user; the axios interceptor auto-refreshes
  access tokens on 401.
- No global state library — keep it simple.
