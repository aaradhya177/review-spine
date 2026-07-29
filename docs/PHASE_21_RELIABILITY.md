# Phase 21: Reliability and Fault Injection

Phase 21 adds reliability primitives:

- async retry with backoff
- circuit breaker
- timeout wrapper
- in-memory idempotency guard

These utilities are intentionally small and testable. Later phases can wire them into provider transports, GitHub posting, workflow nodes, and queue dead-letter handling.

