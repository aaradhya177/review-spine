# Phase 15: GitHub Review Posting

Phase 15 adds the GitHub posting surface.

## Formatter

`format_github_review` converts structured findings into:

- review body
- inline comment payloads

## Client

`GitHubClient` posts review payloads through an injected transport. Tests use a fake transport; later phases can add authenticated GitHub App transport and retry/circuit-breaker wrappers.

The client returns the GitHub review id and raises if GitHub returns a malformed response.

