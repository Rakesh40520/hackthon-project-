# Entity-Relationship Diagram

```text
┌────────────┐         ┌──────────────────────┐
│  User      │         │ RefreshToken         │
│────────────│         │──────────────────────│
│ id (PK)    │ 1     * │ id (PK)              │
│ name       │─────────│ user_id (FK→User)    │
│ email (UQ) │         │ token_hash           │
│ company    │         │ expires_at           │
│ role (ENUM)│         │ revoked              │
│ …          │         └──────────────────────┘
└─────┬──────┘
      │ 1
      │ *
      ▼
┌─────────────────────┐
│ ProcurementProject  │
│─────────────────────│
│ id (PK)             │
│ name                │ 1
│ description         │ *
│ category            │┌────────────────────┐
│ budget              ││ Requirement        │
│ currency            ││────────────────────│
│ deadline            ││ id (PK)            │
│ status (ENUM)       ││ project_id (FK)    │
│ weights × 6         ││ name, description  │
│ created_by (FK→User)││ category, priority │
└────┬────┬───────────┘│ mandatory, weight  │
     │    │            └─────────┬──────────┘
     │    │ 1                    │ 1
     │    │ *                    │ *
     │    ▼                      ▼
     │ ┌─────────────────┐  ┌───────────────────────┐
     │ │ ProjectVendor   │  │ RequirementEvaluation │
     │ │─────────────────│  │───────────────────────│
     │ │ id (PK)         │  │ id (PK)               │
     │ │ project_id (FK) │  │ proposal_id (FK)      │
     │ │ vendor_id (FK)  │  │ requirement_id (FK)   │
     │ │ status          │  │ status (ENUM)         │
     │ └────────┬────────┘  │ score, confidence     │
     │          │ 1         │ reason                │
     │          │ *         │ evidence (doc,page…)  │
     │          ▼           └───────────────────────┘
     │ ┌─────────────────┐         ▲
     │ │ Vendor          │         │
     │ │─────────────────│   ┌─────┴────────────┐
     │ │ id (PK)         │   │ Proposal          │
     │ │ company_name    │   │───────────────────│
     │ │ contact_*,email │   │ id (PK)           │
     │ │ industry        │ 1 │ project_id (FK)   │
     │ │ status          │ * │ vendor_id (FK)    │
     │ └─────────────────┘   │ project_vendor_id │
     │                       │ title, status     │
     │                       │ progress          │
     │                       │ extracted_text    │
     │                       │ analyzed_at       │
     │                       └─┬─┬─┬─┬─┬─┬─┬─┬───┘
     │                         │ │ │ │ │ │ │ │
     │   ┌─────────────────────┘ │ │ │ │ │ │ │
     │   │  ┌────────────────────┘ │ │ │ │ │ │
     │   │  │  ┌───────────────────┘ │ │ │ │ │
     │   │  │  │  ┌──────────────────┘ │ │ │ │
     ▼   ▼  ▼  ▼  ▼                  ▼ ▼ ▼ ▼ ▼
┌────────────────┐  ┌────────────┐  ┌──────────────────┐
│ ProposalDocument│  │ ExtractedField │  │ PricingDetail    │
│────────────────│  │────────────│  │──────────────────│
│ id, proposal_id│  │ id, name   │  │ id, proposal_id  │
│ filename, path │  │ value      │  │ currency         │
│ size, mime     │  │ confidence │  │ year1/year3/year5│
│ checksum       │  │ evidence   │  │ assumptions      │
└────────────────┘  └────────────┘  └──────────────────┘

┌──────────┐  ┌──────────────────┐  ┌──────────────────────┐
│ Risk     │  │ MissingInformation│  │ ClarificationQuestion │
│──────────│  │──────────────────│  │───────────────────────│
│ id       │  │ id               │  │ id, question         │
│ category │  │ field_name       │  │ category, priority   │
│ severity │  │ importance       │  └──────────────────────┘
│ title    │  │ why_it_matters   │
└──────────┘  └──────────────────┘

┌────────────────┐  ┌───────────────────────┐
│ VendorScore    │  │ Recommendation        │
│────────────────│  │───────────────────────│
│ id, proposal_id│  │ id, proposal_id      │
│ total_score    │  │ recommended (bool)   │
│ 6 sub_scores   │  │ rank, decision       │
│ is_eligible    │  │ summary, reasoning   │
│ inelig reasons │  │ strengths, weaknesses│
│ rank, notes    │  │ next_steps (JSON)    │
└───────┬────────┘  └───────────────────────┘
        │ 1
        │ *
┌───────▼────────┐
│ScoringComponent│
│────────────────│
│ name, weight  │
│ raw_score     │
│ weighted_score│
│ explanation   │
└────────────────┘

┌──────────────┐
│ AnalysisJob  │   1 ─ * per Proposal (history)
│──────────────│
│ id, proposal_id (FK)
│ celery_task_id
│ status, current_stage
│ progress, stage_message
│ error_message
│ started_at, completed_at
└──────────────┘

┌────────────┐
│ AuditLog   │
│────────────│
│ id, user_id (FK)
│ action (ENUM)
│ entity_type, entity_id
│ description
│ metadata (JSONB)
│ ip_address, user_agent
│ created_at
└────────────┘
```
