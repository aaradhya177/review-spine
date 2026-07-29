# Phase 9: LLM and Prompt Layer

Phase 9 adds provider-independent LLM plumbing.

## Prompt Registry

`PromptRegistry` loads versioned templates from `backend/app/prompts/templates`.

Current templates:

- `security.v1.md`
- `quality.v1.md`
- `tests.v1.md`
- `docs.v1.md`
- `aggregator.v1.md`

## Model Routing

`ModelRouter` chooses the configured default review model when present, otherwise falls back to local placeholder model names per agent.

## Budget Guard

`BudgetGuard` checks daily spend before LLM calls. If the limit is reached, it raises `BudgetExceededError` before provider cost is incurred.

## LLM Client

`LLMClient` wraps a provider implementing `complete_structured`. It:

- checks budget first
- calls the provider
- records `llm.call` events when an event session is supplied
- preserves prompt version and response schema metadata

The current provider is `FakeLLMProvider`; real provider wiring comes after the contract is stable.

