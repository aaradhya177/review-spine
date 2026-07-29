# Phase 23: CI/CD for AI Changes

Phase 23 adds CI.

## GitHub Actions

`.github/workflows/ci.yml` runs:

- backend tests with Python 3.13
- frontend build with Node 22

## Local Check

Run:

```powershell
.\scripts\check_all.ps1
```

## Prompt and Model Change Rule

Prompt and model-routing changes should include:

- updated prompt template or routing logic
- evaluation case when behavior changes
- passing backend tests
- passing frontend build when UI is affected

