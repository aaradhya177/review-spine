# Phase 12: Specialist Agent Base

Phase 12 adds the shared mechanics for all specialist review agents.

## Contracts

`AgentInput` carries:

- review id
- repository name
- pull request number
- diff text
- changed files

`AgentResult` carries:

- agent type
- validated findings
- confidence
- retrieved evidence
- errors
- metadata

## BaseReviewAgent

`BaseReviewAgent` handles:

- span event emission
- context retrieval
- prompt rendering
- structured LLM calls through `LLMClient`
- timeout and retry loop
- `Finding` validation
- retrieval evidence attachment
- safe error results

Specialist subclasses provide only `agent_type`, `prompt_name`, concern naming, and optional post-processing.

