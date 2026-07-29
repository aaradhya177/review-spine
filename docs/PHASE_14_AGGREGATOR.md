# Phase 14: Aggregator and HITL Routing

Phase 14 adds deterministic aggregation and routing.

## Aggregator

`ReviewAggregator`:

- merges findings from specialist `AgentResult` objects
- deduplicates by file, line range, and category
- keeps the highest-confidence duplicate
- computes overall confidence
- routes the review

## Routing

Routes:

- `auto_post`: confidence is above threshold and there are no critical findings
- `human_review`: confidence is below threshold
- `escalate`: any critical finding exists

When a repository is supplied, the aggregator persists findings, updates review status, and creates a HITL review record for `human_review` or `escalate`.

