# Phase 26: Deployable Infrastructure

Phase 26 adds containerization and local compose infrastructure.

## Files

- `backend/Dockerfile`
- `backend/Dockerfile.worker`
- `frontend/Dockerfile`
- `docker-compose.yml`

## Local Run

```bash
docker compose up --build
```

Services:

- Postgres on `5432`
- Redis on `6379`
- backend API on `8000`
- frontend on `3000`

## Notes

The compose file is local-first. Production should replace local Postgres with Tiger Cloud, configure real secrets, run migrations, and use a production Next.js start command after deployment packaging is finalized.

## Validation

`docker compose config` validates the compose file. Image build requires the Docker daemon to be running.
