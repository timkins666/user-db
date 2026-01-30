# Copilot Instructions for this repository

Purpose: give AI coding agents the minimal, actionable context needed to be productive in this mono-repo.

1. Big-picture architecture

- Three main components:
  - `backend-fastapi/` — Python FastAPI service (primary active backend in docker-compose). Entry: `src/userdb/main.py` (lifespan initializes DB via `userdb.db.init_db()`).
  - `backend-dotnet/` — .NET 9 API implementation (alternate backend). Entry: `api/Program.cs` and endpoints in `api/Endpoints/UserEndpoints.cs`.
  - `frontend/` — Vite + React TypeScript SPA. Entry: `src/main.tsx` and `src/UserManagement.tsx`.

2. Data flow and service boundaries

- Postgres is the canonical DB (see `docker-compose.yml`). Services expect env vars: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`.
- FastAPI: models are `sqlmodel` classes in `backend-fastapi/src/userdb/models/user.py` and DB is managed in `backend-fastapi/src/userdb/db.py`. Routes live in `backend-fastapi/src/userdb/routers/`.
- .NET: EF Core `PostgresDbContext` maps to table `user` (see `backend-dotnet/api/Models/DBContext.cs`). Endpoints return DTOs in `api/Endpoints`.
- Frontend communicates with backend via axios client at `frontend/src/services/api.ts` which uses baseURL `/api` and implements token refresh/queue logic — review that file before changing auth behavior.

3. Project-specific conventions and patterns

- Soft-delete: both backends use a `deleted` boolean flag instead of hard deletes (FastAPI: `User.deleted`; .NET: `User.Deleted`). Follow this when implementing delete logic.
- Validation duplication: business validation exists in both server implementations (FastAPI uses pydantic/SQLModel validators in `UserCreate`; .NET uses `ValidateUser` in `UserEndpoints`). Mirror rules to keep parity.
- DB init behaviour: `backend-fastapi` will call `SQLModel.metadata.create_all(engine)` on startup. The `REFRESH_DB` env var (checked in `db.py`) will drop and recreate tables — useful for dev reset.
- CORS: both backends whitelist `http://localhost:5173` (frontend dev server).

4. Developer workflows & commands

- Full stack (recommended for quick dev):
  - From repo root: `docker compose up --build` (starts Postgres, backend-fastapi, frontend as configured in `docker-compose.yml`).
- FastAPI local dev / tests:
  - Install project deps from `backend-fastapi/pyproject.toml` and run tests with `pytest` from `backend-fastapi/`.
  - Docker runs FastAPI with `/app/.venv/bin/fastapi run ./src/userdb/main.py --port 80` (see `backend-fastapi/Dockerfile`). Use docker-compose for parity.
- Frontend local dev:
  - `cd frontend && npm install && npm run dev` (serves on :5173). Tests: `npm run test`.
- .NET backend and tests:
  - `cd backend-dotnet/api && dotnet run` to run API. Tests: `cd backend-dotnet/api-tests && dotnet test`.

5. Integration points & gotchas

- Axios baseURL: `frontend/src/services/api.ts` sets `baseURL: "/api"`. If the dev setup does not proxy `/api` to the backend, requests may need an explicit backend URL or a Vite proxy configured in `vite.config.ts`.
- JWT/auth: FastAPI registers `userdb.middleware.jwt_auth_middleware` in `main.py`. The frontend token + refresh logic lives in `frontend/src/auth/*`. Coordinate changes to both sides when modifying auth flow.
- Table/column naming: the .NET model maps DB column names explicitly (lowercase names). If you alter schema, keep migrations/column names in sync to avoid subtle mismatches.

6. Where to add code

- FastAPI routes: add routers under `backend-fastapi/src/userdb/routers/` and register them in `main.py`.
- C# endpoints: extend `api/Endpoints/UserEndpoints.cs` and keep DTOs in `api/Models/Dto`.
- Frontend: UI components live in `frontend/src/components/`; data hooks in `frontend/src/hooks` and service calls in `frontend/src/services/`.

7. Quick pointers for PRs and tests

- Keep API parity between FastAPI and .NET for user validation/shape where both are maintained.
- When changing DB schema, update both `backend-fastapi` models and `.NET` `OnModelCreating` mapping if you intend to keep both backends supported.

If anything here is unclear or you'd like more examples (e.g., how to wire a new endpoint end-to-end), tell me which area to expand and I'll iterate.
