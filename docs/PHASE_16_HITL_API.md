# Phase 16: Human Approval Queue API

Phase 16 adds the first HITL API surface.

## Endpoints

- `GET /hitl/reviews`
- `GET /hitl/reviews/{hitl_id}`
- `POST /hitl/reviews/{hitl_id}/approve`
- `POST /hitl/reviews/{hitl_id}/reject`
- `POST /hitl/reviews/{hitl_id}/escalate`
- `POST /hitl/reviews/{review_id}/dispute`

The router depends on a `HitlService` protocol. Tests use `InMemoryHitlService`; later infrastructure can inject a repository-backed implementation.

