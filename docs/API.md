# API Reference

The API is documented interactively at `/docs` (Swagger UI) and `/redoc` once
the backend is running. Below is a concise summary.

## Auth

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| POST   | /api/auth/register      | –            | Create user, return access+refresh tokens |
| POST   | /api/auth/login         | –            | Email/password login |
| POST   | /api/auth/refresh       | refresh-body | New access token |
| POST   | /api/auth/logout        | refresh-body | Revoke refresh token |
| GET    | /api/auth/me            | Bearer       | Current user |
| PATCH  | /api/auth/me            | Bearer       | Update name/company |
| POST   | /api/auth/change-password | Bearer     | Change password |

## Projects

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET    | /api/projects                       | List (filter by status) |
| POST   | /api/projects                       | Create |
| GET    | /api/projects/{id}                  | Detail |
| PATCH  | /api/projects/{id}                  | Update (incl. weights) |
| DELETE | /api/projects/{id}                  | Delete |
| GET    | /api/projects/{id}/vendors          | List linked vendors |
| POST   | /api/projects/{id}/vendors          | Add vendor |
| PATCH  | /api/projects/{id}/vendors/{pvId}   | Update link status |
| DELETE | /api/projects/{id}/vendors/{pvId}   | Remove link |
| GET    | /api/projects/{id}/requirements     | List |
| POST   | /api/projects/{id}/requirements     | Create |
| PATCH  | /api/projects/{id}/requirements/{rId} | Update |
| DELETE | /api/projects/{id}/requirements/{rId} | Delete |

## Vendors

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET    | /api/vendors         | List (search/filter) |
| POST   | /api/vendors         | Create |
| GET    | /api/vendors/{id}    | Detail |
| PATCH  | /api/vendors/{id}    | Update |
| DELETE | /api/vendors/{id}    | Delete |

## Proposals

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET    | /api/proposals                       | List (filter by project) |
| POST   | /api/proposals/upload                | Multipart upload (project_id, vendor_id, file) |
| GET    | /api/proposals/{id}                  | Full detail (extracted fields, evaluations, risks, score, recommendation) |
| POST   | /api/proposals/{id}/reanalyze        | Re-run pipeline |
| GET    | /api/proposals/{id}/job              | Latest job status |
| POST   | /api/proposals/{id}/clarify          | Regenerate clarification questions |
| DELETE | /api/proposals/{id}                  | Delete |

## Analysis

| Method | Path | Description |
| ------ | ---- | ----------- |
| POST   | /api/analysis/run/{proposalId}   | Queue a single analysis |
| POST   | /api/analysis/rescore/{projectId}| Recompute scores for all proposals in project |

## Comparison

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET    | /api/comparison/{projectId} | Side-by-side comparison + ranking |

## Recommendations

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET    | /api/recommendations/{projectId} | List all (sorted by rank) |
| GET    | /api/recommendations/{projectId}/top | Top recommendation |
| POST   | /api/recommendations/regenerate/{proposalId} | Regenerate |

## AI Copilot

| Method | Path | Description |
| ------ | ---- | ----------- |
| POST   | /api/copilot/chat | Send a chat (project_id, messages, optional vendor_id) |

## Reports

| Method | Path | Description |
| ------ | ---- | ----------- |
| POST   | /api/reports/{projectId} | Returns PDF or XLSX (`{ format: "pdf" \| "xlsx" }`) |

## Dashboard

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET    | /api/dashboard/summary | KPIs, charts data, recent projects |

## Audit

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET    | /api/audit | Paginated audit log |
