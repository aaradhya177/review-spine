# Phase 5: Queue Worker

The webhook ingress enqueues `ReviewJob` payloads through the `ReviewQueue` protocol. Production uses `ARQReviewQueue`; tests and local dependency-free flows can use `InMemoryReviewQueue`.

## Job Shape

`ReviewJob` carries:

- `delivery_id`
- `repo_full_name`
- `pull_request_number`
- `head_sha`
- `base_sha`
- `webhook_event_id`

The stable ARQ job id is `review:{delivery_id}`. This supports idempotent enqueue behavior and makes worker logs easy to correlate with webhook deliveries.

## Worker

The worker entrypoint is `app.job_queue.arq_worker.WorkerSettings`.

Local command:

```powershell
.\scripts\run_worker.ps1
```

ARQ settings:

- `max_jobs = 10`
- `job_timeout = 300`
- `max_tries = 3`
- `retry_jobs = True`
- `queue_name = "review-spine"`

## Lifecycle Recording

`run_review_job` records:

- `started`
- `completed`
- `failed`

The current recorder is an interface with an in-memory implementation. Phase 8 will replace this with the durable `agent_events` spine.

## Dead-Letter Strategy

Failures are recorded and re-raised so ARQ can apply retry policy. Jobs that exhaust retries remain inspectable through ARQ/Redis operational tooling. Phase 21 will add the full reliability layer and explicit dead-letter handling.

