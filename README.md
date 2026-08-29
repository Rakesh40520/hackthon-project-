# 🛡️ ClauseGuard
### Verified Contract Intelligence

**Extract what matters. Verify what the AI claims.**

ClauseGuard is a web application that extracts the commercially important terms
from a contract — then does something most AI contract tools never do: it
**deterministically verifies** every AI claim against the actual source
document, and **independently recalculates** the total cost of ownership
instead of trusting the model's arithmetic.

> Most AI contract tools ask the model to read the contract and trust its answer.
> ClauseGuard treats the model as an untrusted extractor. It checks the evidence
> itself and independently verifies the math.

*ClauseGuard helps organize and verify contract information. It does not provide legal advice.*

---

## 1. What ClauseGuard does

1. **Structured extraction** — Upload a contract (PDF / TXT / DOCX). An LLM
   extracts 19 commercial, metadata and risk fields (vendor, term, fees,
   renewal, termination, liability cap, governing law, …).
2. **Source-grounded evidence** — Every extracted field must carry a verbatim
   `evidence_quote` copied from the contract.
3. **Deterministic verification** — Plain Python code checks whether that quote
   actually exists in the document. The LLM is never asked to grade its own work.
4. **TCO arithmetic cross-check** — ClauseGuard independently recalculates the
   total contract cost from structured numbers (exact `Decimal` arithmetic) and
   compares it with the AI-reported total.
5. **Loud failures** — Invented quotes, misquotes and unsupported claims are
   surfaced in a dedicated **"Claims Requiring Attention"** section. Nothing is
   hidden, and confidence scores are never allowed to upgrade a failed check.

## 2. The problem

> LLMs can confidently produce plausible contract analysis that is not
> supported by the document.

A model can assert *"Termination requires 90 days' notice"* with 97% confidence
while the contract actually says *30 days*. It can report a total cost of
*$50,000* when the extracted pricing terms arithmetically total *$34,000*.
For procurement, finance and founders, that gap between *plausible* and
*supported* is where real money is lost.

## 3. The solution

> Every important AI claim is paired with source evidence and independently
> verified.

- AI output is treated as **untrusted input**, not as an answer.
- `verify()` is **deterministic Python** — same input, same result, no model
  in the loop, no hallucinated second opinion.
- Money math uses **`Decimal`**, shown step by step, so a human can audit it.

## 4. How the deterministic `verify()` layer works

```python
from core.verifier import normalize, verify

result = verify(evidence_quote, source_text)
# result.status:      VERIFIED | UNVERIFIED | NO_EVIDENCE
# result.match_found: bool
# result.message:     human-readable explanation
```

1. Both strings are **normalized**: Unicode NFKC, curly quotes → straight
   quotes, dashes and exotic spaces unified, zero-width characters stripped,
   lowercased, whitespace collapsed.
2. The normalized quote is checked as an **exact substring** of the normalized
   source.
3. Outcomes:
   - `VERIFIED` — *"Evidence was found in the uploaded contract."*
   - `UNVERIFIED` — *"The AI-provided evidence could not be found verbatim in
     the uploaded contract. This claim should not be treated as confirmed."*
   - `NO_EVIDENCE` — *"No source evidence was supplied for this claim."*
4. **Confidence is not an input.** A 99%-confident claim with unsupported
   evidence stays `UNVERIFIED`. There is no code path that upgrades it.

When a claim verifies, ClauseGuard also locates the match in the raw text and
shows the **surrounding source context** so a human can confirm it in seconds.

## 5. How the TCO cross-check works

`core/tco_calculator.py` computes the total from structured inputs using
`Decimal` arithmetic — never the model's math:

```
Setup fee:                              $10,000.00
Recurring fee: $2,000.00 × 12 month(s) = $24,000.00
Total contract cost:                    $34,000.00
```

It then compares:

| Status | Meaning |
|---|---|
| `MATCH` | AI-reported total agrees with the arithmetic (within a tiny rounding tolerance) |
| `DISAGREEMENT` | AI-reported total differs materially → **⚠ Arithmetic disagreement detected** banner |
| `INSUFFICIENT_DATA` | Pricing is missing/ambiguous → no calculation is fabricated, warnings explain why |
| `AI_TCO_NOT_PROVIDED` | Calculation succeeded but the model reported no total; deterministic figure shown for reference |

Ambiguity is handled conservatively: *"Fees may vary based on usage"*,
*"Pricing to be mutually agreed"*, ranges, and multiple differing amounts
produce **warnings, never guesses**. Unit-priced usage (e.g. `$0.002 per
query`) is excluded from totals with an explanatory note.

## 6. Architecture

```
clauseguard/
│
├── app.py                      # Streamlit UI (orchestration & rendering only)
├── requirements.txt
├── .env.example                # copy to .env and add your API key
├── README.md
│
├── core/                       # deterministic business logic (no LLM calls)
│   ├── schemas.py              # Pydantic models + field registry
│   ├── verifier.py             # normalize() + verify() — the differentiator
│   └── tco_calculator.py       # independent Decimal arithmetic
│
├── services/
│   ├── document_parser.py      # PDF (pypdf) / DOCX (python-docx) / TXT
│   ├── llm_extractor.py        # OpenAI-compatible extraction, strict prompt
│   ├── number_parser.py        # conservative money/term/frequency parsing
│   └── demo_fixture.py         # simulated unreliable extraction (demo only)
│
├── utils/
│   └── formatting.py           # money/label/status formatting
│
├── sample_data/
│   └── sample_contract.txt     # demo contract (MSA with clear pricing terms)
│
└── tests/
    ├── test_acceptance.py      # the 7 acceptance criteria + parser tests
    └── test_app_render.py      # UI smoke tests (Streamlit AppTest)
```

The LLM has exactly one job: propose structured fields with verbatim evidence.
Everything downstream — verification, arithmetic, statuses, warnings — is
deterministic code.

## 7. Installation

Requires **Python 3.11+**.

```bash
# 1. (optional but recommended) create a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. configure your API key
copy .env.example .env        # Windows  (macOS/Linux: cp .env.example .env)
# then edit .env and set OPENAI_API_KEY=sk-...
```

No database, no external services, no manual setup — everything runs locally.

## 8. Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | For live extraction | Your OpenAI API key (demo mode works without it) |
| `LLM_BASE_URL` | No | Any OpenAI-compatible endpoint (Groq, Together, Ollama, OpenRouter, …) |
| `LLM_MODEL` | No | Chat model for extraction (default: `gpt-4o-mini`) |
| `LLM_TIMEOUT` | No | Request timeout in seconds (default: `120`) |

Secrets are only ever read from the environment / `.env` file. Nothing is
hardcoded; `.env` is git-ignored.

## 9. Running the application

```bash
streamlit run app.py
```

Then open the printed local URL (usually `http://localhost:8501`).

## 10. Demo walkthrough (2 minutes)

1. **Launch the app.** No API key needed for the demo path.
2. Click **🧪 Run built-in demo instead** — this loads the bundled
   `sample_data/sample_contract.txt` and a *simulated, deliberately unreliable*
   extraction (clearly labeled in the UI).
3. **Summary Dashboard** — show the metrics: fields extracted, verified,
   unverified, no-evidence, TCO status.
4. **Extracted Terms** — open a green `✓ Verified` row (e.g. *Renewal terms*):
   the evidence quote, its verification, and the surrounding source context
   from the actual document are shown.
5. **Claims Requiring Attention** — the centerpiece: the AI claims
   *"Termination requires 90 days' written notice"* with **0.97 confidence**,
   but the contract says **thirty (30) days**. ClauseGuard flags:
   - ⚠ AI claim could not be verified
   - the claimed evidence quote that does **not** exist anywhere in the document
   - why verification failed — and notes that confidence does not override it.
6. Say the line: *"Model confidence is the AI grading its own homework.
   ClauseGuard grades against the document instead."*
7. **Independent TCO Cross-Check** — the AI reported **$50,000**. Deterministic
   arithmetic: $10,000 setup + $2,000 × 12 = **$34,000**. The red banner reads:
   **⚠ Arithmetic disagreement detected — Difference: $16,000.00**.
8. Conclude:

   > "The AI helps us read the contract. The software verifies what the AI says."

**Live mode:** upload any PDF/TXT/DOCX contract, keep *Live LLM extraction*
selected in the sidebar, and press **Analyze & Verify Contract**. Results
depend on the model — and that is the point: whatever it claims gets checked.

## 11. Acceptance criteria (all automated in `tests/`)

| # | Criterion | Where |
|---|---|---|
| 1 | Real evidence quote present in the contract → `VERIFIED` | `test_acceptance_1` |
| 2 | Evidence quote not present → `UNVERIFIED` | `test_acceptance_2` |
| 3 | High confidence cannot upgrade `UNVERIFIED` → `VERIFIED` | `test_acceptance_3` |
| 4 | $10,000 + $2,000 × 12 = **$34,000** exactly | `test_acceptance_4` |
| 5 | AI-reported $50,000 vs calculated $34,000 → `DISAGREEMENT` ($16,000 diff) | `test_acceptance_5` |
| 6 | Ambiguous pricing → `INSUFFICIENT_DATA` / warnings, never fabricated numbers | `test_acceptance_6` |
| 7 | Upload → extraction → verification → TCO runs with no DB / manual setup | `test_acceptance_7` + `test_app_render` |

Run the test suites:

```bash
python tests/test_acceptance.py
python tests/test_app_render.py
# (pytest is also supported if you have it installed: pytest tests/)
```

## 12. Error handling

Graceful (no raw stack traces in the UI; developer detail is in the **Debug
details** expander at the bottom):

- Missing API key → actionable message + demo-mode suggestion
- Unsupported file type / empty file
- Scanned or image-only PDF (no extractable text)
- Text too short to analyze
- LLM timeout / connection errors / invalid JSON / schema mismatches
- Missing evidence → `NO_EVIDENCE` displayed, never hidden
- Missing or ambiguous pricing → `INSUFFICIENT_DATA` with explicit warnings


