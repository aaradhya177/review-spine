# Phase 26: Deployable Infrastructure

Phase 26 adds containerization and local compose infrastructure.

## Files

- `backend/Dockerfile`
- `backend/Dockerfile.worker`
- `frontend/Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

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

The worker reads `REDIS_URL` through ARQ's `redis_settings`, so in compose it connects to the Redis service instead of container-local `localhost`. `.dockerignore` keeps local `node_modules`, Next.js build output, caches, logs, and local env files out of image build contexts.

## Validation

`docker compose config` validates the compose file. With Docker running, `docker compose build backend worker frontend` builds the service images and `docker compose up -d` starts Postgres, Redis, backend, worker, and frontend.
