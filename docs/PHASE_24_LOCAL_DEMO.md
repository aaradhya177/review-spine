# Phase 24: End-to-End Local Demo

Phase 24 adds a local webhook simulation.

Run:

```powershell
.\scripts\simulate_webhook.ps1
```

The script:

- loads `fixtures/pull_request_opened.json`
- signs it with an HMAC test secret
- posts it to the FastAPI webhook route through `TestClient`
- uses in-memory idempotency and queue adapters
- prints the queued review job

No external credentials are required.

