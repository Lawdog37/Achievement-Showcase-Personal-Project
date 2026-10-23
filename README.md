# Achievement Showcase

This project's goal is to let you efficiently track achievements for all games across all launchers. Steam is the baseline, with other launchers to follow.

It shows your **rarest achievements** in a showcase, your **progress** toward 100% in each game, the **easiest achievements you're missing**, and your unlock history over time.

![CI](https://github.com/Lawdog37/Achievement-Showcase-Personal-Project/actions/workflows/ci.yml/badge.svg)

## Quick start (Docker)

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/) and a free [Steam Web API key](https://steamcommunity.com/dev/apikey).

1. Clone the repo:
   ```bash
   git clone https://github.com/Lawdog37/Achievement-Showcase-Personal-Project.git
   cd Achievement-Showcase-Personal-Project
   ```
2. Create your settings file and put your API key in it:
   ```bash
   cp .env.example .env
   ```
3. Start it:
   ```bash
   docker compose up --build
   ```
4. Open **http://localhost:8080**, enter a Steam profile, and click **Sync now**.

The Steam profile's **Game details** must be set to **Public** (Steam → Edit Profile → Privacy Settings).

## Tech stack

| Part | Tools |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy, Alembic, SQLite, httpx |
| Frontend | React, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router, Recharts |
| Quality | pytest, respx, Ruff, Vitest, Prettier, oxlint, pre-commit, GitHub Actions |
| Packaging | Docker, Docker Compose, nginx |

## Development setup

For working on the code with instant reloads.

**Backend** (needs Python 3.13):
```bash
python -m venv .venv
source .venv/Scripts/activate     # Windows Git Bash; macOS/Linux: source .venv/bin/activate
cd backend
pip install -e ".[dev]"
alembic upgrade head
fastapi dev app/main.py           # http://127.0.0.1:8000/docs
```

**Frontend** (needs Node 24), in a second terminal:
```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

**Sync from the command line:** `python -m app.sync` (from `backend/`; uses `STEAM_ID` from `.env`).

## Tests and checks

```bash
cd backend && pytest && ruff check . && ruff format --check .
cd frontend && npm test && npm run lint && npm run format:check && npm run build
```

`pre-commit install` runs the formatters and linters on every commit. GitHub Actions runs everything on every push.

## Project structure

```
backend/
  app/            FastAPI app: models, queries, Steam client, sync service, API routes
  alembic/        database migrations
  tests/          pytest suite (Steam is faked with respx)
frontend/
  src/            React app: pages, components, API client, hooks
compose.yaml      runs both with Docker
```

## Troubleshooting

| Problem | Fix |
|---|---|
| Docker says virtualization is disabled | Turn on **SVM Mode** (AMD) or **Intel VT-x** in your BIOS/UEFI |
| "STEAM_API_KEY is not set" | Create `.env` from `.env.example` and add your key, then `docker compose up -d` |
| "This Steam profile is private" | Set the profile and **Game details** to Public in Steam |
| Port 8080 is already in use | Change `"8080:80"` in `compose.yaml` to e.g. `"8081:80"` |

## License

MIT. See [LICENSE](LICENSE).
