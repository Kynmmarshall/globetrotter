# GlobeTrotter

A travel discovery and itinerary planning app for Yaoundé, Cameroon, built as
a two-phase systems design exercise: a **Phase 1 monolith** (single FastAPI
process, JSON file storage) and a **Phase 2 microservices** architecture
(three independent FastAPI services + an Nginx API gateway + RabbitMQ + a
React frontend). See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full design.

## Architecture at a glance

- **Frontend** (`frontend/`): React + TypeScript + Vite, TanStack Query,
  React Router, Tailwind CSS, Leaflet/OpenStreetMap. Talks **only** to the
  microservices, through the gateway.
- **Monolith** (`backend/monolith/`): standalone FastAPI app, JSON file
  storage. Demonstrates the assignment's Phase 1 baseline. Not used by the
  frontend.
- **Microservices** (`backend/microservice/`):
  - `user_service/` — auth, profile, favourites, global chat (WebSocket)
  - `recommendation_service/` — destination catalogue, recommendations,
    driving directions (OSRM), serves destination images
  - `itinerary_service/` — trip planning, ordered stops, sharing
  - `gateway/` — Nginx reverse proxy, the only public entry point
  - Each service persists its own JSON file (`app/store.py`) — no database
    server. RabbitMQ carries domain events between services (an outbox
    pattern, so a broker outage delays events instead of losing them).

## Prerequisites

- Docker Desktop
- Node.js 20+ (for frontend development outside Docker)
- Python 3.11+ (for backend development outside Docker)

## Quick start (full stack via Docker Compose)

```powershell
# From the repo root
Copy-Item .env.example .env
python scripts/generate_jwt_keys.py          # one-time RS256 keypair for JWTs
python scripts/build_destination_assets.py   # generates destination images + seed data

docker compose --env-file .env -f infra/compose.microservices.yml up -d --build
```

Then open **http://localhost:8090** (the gateway; change with `GATEWAY_PORT`
in `.env` if 8090 is taken on your machine).

To stop everything: `docker compose -f infra/compose.microservices.yml down`.

## Running the Phase 1 monolith (standalone)

```powershell
docker compose -f infra/compose.monolith.yml up -d --build
```

Open **http://localhost:8000/docs** for the OpenAPI UI (no separate frontend
for the monolith — it is a backend-only demonstration).

## Local development (faster iteration than full Docker rebuilds)

Each backend service has its own virtual environment and is independently
runnable:

```powershell
cd backend/microservice/user_service
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q          # run tests
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8001
```

(Repeat for `recommendation_service` on port 8002 and `itinerary_service` on
port 8003, and `backend/monolith` on port 8000.) Start `infra/compose.microservices.yml`
for just RabbitMQ if you want events working while running services on the host.

Frontend:

```powershell
cd frontend
npm install
npm run dev       # http://localhost:5173, proxies /api and /ws to the gateway
npm run lint
npm run build
```

The dev server proxies `/api`, `/static`, and `/ws` to
`http://localhost:8090` by default (override with `VITE_GATEWAY_URL`), so it
works whether the gateway/services run in Docker or directly on the host.

## Testing

Each backend service has its own test suite (pytest, no shared fixtures
between services):

```powershell
cd backend/monolith; .venv\Scripts\python -m pytest -q                              # 17 tests
cd backend/microservice/user_service; .venv\Scripts\python -m pytest -q             # 21 tests
cd backend/microservice/recommendation_service; .venv\Scripts\python -m pytest -q   # 15 tests
cd backend/microservice/itinerary_service; .venv\Scripts\python -m pytest -q        # 19 tests
```

Frontend: `npm run build` (type-checks) and `npm run lint`.

## Repository layout

See [PROJECT_PLAN.md](PROJECT_PLAN.md) section 4 for the full intended
structure and section 16 for the deliverables/definition of done.

## Known simplifications (documented, not oversights)

- Destination names/categories/coordinates for the seed catalogue are
  **provisional** — see [PROJECT_PLAN.md](PROJECT_PLAN.md) section 10.
- JWT revocation (logout-everywhere, bans) takes effect only when a service
  other than User Service re-validates a token at its natural expiry
  (`JWT_ACCESS_TOKEN_MINUTES`), since Recommendation/Itinerary Services
  verify tokens with only the public key and don't call back to User Service.
- No dead-letter queue yet for the two durable RabbitMQ consumers
  (Recommendation's preference consumer, Itinerary's destination consumer) —
  a permanently failing message is retried indefinitely instead of parked.
- Directions use the public OSRM demo server by default
  (`OSRM_BASE_URL`); see PROJECT_PLAN.md section 11 for the self-hosting path.
