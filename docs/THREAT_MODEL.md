# Threat Model

## Assets

- GitHub App credentials
- OpenAI/provider credentials
- Tiger/Postgres connection string
- source code retrieved into prompts
- review findings and audit events

## Primary Threats

- forged GitHub webhooks
- duplicate webhook replay
- prompt injection inside pull request text or repository files
- secrets leaking into logs, events, traces, or UI
- unauthorized dashboard actions
- LLM/tool calls exceeding intended scope

## Current Controls

- HMAC verification for GitHub webhooks
- delivery idempotency key
- secret masking utility
- prompt-injection phrase assessment
- RBAC dependency hook
- no raw provider SDK usage in business logic
- fake/local providers for tests

## Remaining Work

- production auth provider integration
- repository-backed RBAC
- signed audit trail immutability controls
- sandbox capability scopes for tool execution
- richer prompt-injection classifier and policy response

