# Procurement Intelligence Platform

## Procurement Teams Struggled to Compare Vendor Proposals

**Problem:** Companies received proposals from multiple vendors with different pricing structures, terms, features, and conditions. Comparing them manually was time-consuming and made it easy to overlook important differences.

**Build:** An AI agent that analyzes vendor proposals, extracts important commercial and technical details, compares vendors against predefined requirements, highlights risks or missing information, and recommends the strongest options.

---

## Key Capabilities

1. **Commercial & Technical Extraction:** Upload PDF, DOCX, XLSX, CSV, or TXT vendor proposals. The AI agent extracts contact details, SLAs, hosting options, security features, compliance standards, and line-item costs.
2. **Requirements Evaluation:** Define technical, commercial, security, compliance, and support criteria. The AI evaluates each vendor (MEETS, PARTIALLY_MEETS, DOES_NOT_MEET) with exact document citations.
3. **Risk & Missing Info Detection:** Highlights hidden vendor risks (auto-renewal clauses, uncapped price increases, termination penalties, missing SLAs) and flags critical missing data (disaster recovery RTO/RPO, data residency).
4. **Pricing Normalization:** Calculates 1-year, 3-year, and 5-year Total Cost of Ownership (TCO).
5. **Objective Scoring & Recommendations:** Computes weighted scores across 6 dimensions, disqualifies vendors failing mandatory requirements, and generates explainable recommendations on the strongest options.
6. **Comparison Matrix & AI Copilot:** Side-by-side vendor comparison matrix with charts, plus an interactive AI Copilot to answer questions with document citations.
7. **Audit & Reporting:** Export executive-ready PDF and Excel reports.

---

## Quick Start

### 1. One-Click Startup (Windows)
Double-click `start_all.bat` or run:
```powershell
.\start_all.ps1
```

### 2. Manual Startup

**Backend:**
```bash
cd backend
..\.venv\Scripts\python.exe -m app.db_init
..\.venv\Scripts\python.exe -m app.seed
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Service URLs & Demo Credentials

| Service | URL |
| --- | --- |
| **Frontend UI** | [http://localhost:5173](http://localhost:5173) |
| **Backend API & Swagger Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) |

**Demo Login Credentials:**
- **Email:** `admin@procurement.dev`
- **Password:** `Admin123!`

---

## AI Providers

Configure in `backend/.env`:
- `AI_PROVIDER=mock` (Zero API keys required, works offline)
- `AI_PROVIDER=openai` (GPT-4o, GPT-4o-mini)
- `AI_PROVIDER=anthropic` (Claude 3.5 Sonnet, Claude 3.5 Haiku)
- `AI_PROVIDER=gemini` (Gemini 1.5 Pro / Flash)
- `AI_PROVIDER=ollama` (Local LLMs)

---

## Testing

```bash
cd backend
..\.venv\Scripts\python.exe -m pytest
```