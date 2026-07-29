# Product Contract

## Purpose

Review Spine exists to reclaim scarce senior-engineer review attention. It automates the mechanical, repeatable parts of pull-request review while routing uncertain, critical, or disputed cases to humans.

The product optimizes for selective, high-value findings. It should not flood a pull request with every possible nit. A quiet, correct reviewer is better than a noisy one that trains developers to ignore it.

## Trigger

The primary trigger is a GitHub `pull_request` webhook for these actions:

- `opened`
- `synchronize`
- `reopened`
- future: `ready_for_review`

The ingress service must validate the GitHub HMAC signature, check the `X-GitHub-Delivery` idempotency key, enqueue work, and acknowledge quickly. It must not run review work inline.

## Output

The primary output is one structured review for a GitHub pull request.

The review may be:

- posted automatically to GitHub
- held in a human approval queue
- escalated because it contains a critical finding
- recorded as failed with a traceable reason

## Review Concerns

The system reviews through four specialist concerns:

- `security`: exploitable issues, auth bypasses, injection risks, secrets, unsafe deserialization
- `quality`: correctness, logic errors, edge cases, maintainability, complexity, API misuse
- `tests`: missing coverage, brittle assertions, untested edge cases, regression risk
- `docs`: public API documentation, stale comments, missing rationale, unclear conventions

## Finding Contract

Every agent returns structured findings, not free-form prose. A finding must include:

- `id`: stable identifier
- `review_id`: review identifier
- `agent_type`: `security`, `quality`, `tests`, or `docs`
- `severity`: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `INFO`
- `category`: concise issue class
- `summary`: short developer-facing finding
- `file_path`: target file
- `line_start`: first relevant line
- `line_end`: optional last relevant line
- `suggestion`: concrete remediation when available
- `confidence`: number from `0.0` to `1.0`
- `rationale`: why the finding exists
- `evidence`: retrieved context, prompt version, or supporting metadata

Findings are auditable units. The aggregator merges and deduplicates them, but must preserve enough evidence to explain why the final review was produced.

## Autonomy Level

The default autonomy level is `human handles exceptions`.

Routing rules:

- Auto-post when overall confidence is at or above the configured threshold and there are no `CRITICAL` findings.
- Route to human approval when confidence is below threshold.
- Escalate when any `CRITICAL` finding exists, regardless of confidence.
- Route developer disputes into a dispute workflow and record feedback.

Autonomy should be earned over time through evaluation, audits, and production behavior. It should not be expanded by default.

## Proof Requirement

The system must be able to reconstruct every review from durable events ordered by time. At minimum, it records:

- webhook receipt and idempotency decision
- queue job lifecycle
- workflow node start/end
- retrieval requests and selected context
- LLM calls, prompt versions, token counts, latency, and cost
- findings produced
- aggregation and routing decisions
- GitHub posting result
- human approval, rejection, dispute, or escalation

## Non-Goals

This project does not aim to:

- replace human ownership of code quality
- auto-merge pull requests
- run arbitrary untrusted code without sandboxing
- perform broad repository refactors
- guarantee full vulnerability detection
- optimize for maximum comment volume
- require multiple durable databases before the data shape proves it

