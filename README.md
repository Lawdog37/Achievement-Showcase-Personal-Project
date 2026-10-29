# Achievement Showcase

Track your Steam achievements and show off the rare ones. Sign in through Steam, sync your library, and see your **rarest achievements**, how close you are to **100%** in every game, the **easiest achievements you're still missing**, and which popular games people are finishing right now.

Steam is the starting point; other launchers may follow.

![CI](https://github.com/Lawdog37/Achievement-Showcase-Personal-Project/actions/workflows/ci.yml/badge.svg)

## Contents

- [What it does](#what-it-does)
- [Before you start](#before-you-start)
- [Quick start with Docker](#quick-start-with-docker)
- [Using the app](#using-the-app)
- [Development setup](#development-setup)
- [Configuration (`.env`)](#configuration-env)
- [Command reference](#command-reference)
- [Tests and code quality](#tests-and-code-quality)
- [Changing the database](#changing-the-database)
- [Backups](#backups)
- [Deploying to a server](#deploying-to-a-server)
- [Security](#security)
- [Project structure](#project-structure)
- [API reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Working on the code](#working-on-the-code)
- [License](#license)

## What it does

| Page | What you see |
|---|---|
| **Overview** (home) | Steam's most-played games today and how hard each is to 100%, games trending toward 100%, and a "welcome back" card with your hunts |
| **Profile** | Headline stats, your rarest achievements, closest-to-100% games, easiest missing achievements, and unlocks per month |
| **Near completion** | Every game with achievements, filtered (in progress, completed, not started) and sorted |
| **Hunting** | The games you've chosen to go for, each with every locked achievement, easiest first |
| **Privacy** | What's stored, and a **Delete my data** button |

Anyone can view a synced profile. Only the signed-in owner can sync it or change its hunt list.

## Before you start

You need:

1. **A Steam Web API key.** Get one free at [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey). For "Domain name", `localhost` is fine. Steam only gives keys to accounts that have spent at least $5.
2. **Public Steam privacy settings** for any profile you want to sync. In Steam, go to **profile → Edit Profile → Privacy Settings**:
   - **My profile:** Public
   - **Game details:** Public (without this, Steam won't share which achievements are unlocked)
   - **"Always keep my total playtime private"**: unticked
3. **[Git](https://git-scm.com/downloads)**.
4. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (Windows or Mac) or Docker Engine (Linux), with Docker Compose **2.24 or newer**.
   - On Windows, Docker needs hardware virtualization: **SVM Mode** (AMD) or **Intel VT-x**, switched on in the BIOS/UEFI.
   - Open Docker Desktop once and wait for **Engine running** before continuing.

## Quick start with Docker

This runs the whole app (database, API, daily job and website) with one command.

**1. Download the code:**
```bash
git clone https://github.com/Lawdog37/Achievement-Showcase-Personal-Project.git
```
```bash
cd Achievement-Showcase-Personal-Project
```

**2. Create your settings file** from the template:
```bash
cp .env.example .env
```

**3. Fill in three values in `.env`.** Generate the two random ones with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

| Setting | Value |
|---|---|
| `STEAM_API_KEY` | your key from Steam |
| `SECRET_KEY` | one random value from the command above |
| `POSTGRES_PASSWORD` | a **different** random value |

Leave the other lines as they are. `.env` is never committed to Git.

**4. Start it.** The first build takes a few minutes:
```bash
docker compose up -d --build
```

**5. Open http://localhost:8080**, click **Sign in through Steam**, and sign in on Steam's page. You'll land on your profile. Click **Sync now**; the first sync takes 1–3 minutes, depending on library size.

**What's running** (`docker compose ps`):

| Container | Job |
|---|---|
| `db` | Postgres database (data kept in a Docker volume) |
| `backend` | The API; applies database migrations every time it starts |
| `scheduler` | Runs the daily job at startup and every day at 06:00 UTC |
| `frontend` | nginx: serves the website at port 8080 and passes `/api` to the backend |

**Everyday commands:**

| Command | What it does |
|---|---|
| `docker compose up -d --build` | Start, or rebuild after code changes |
| `docker compose ps` | What's running, and whether it's healthy |
| `docker compose logs -f backend` | Follow a container's logs (Ctrl+C to stop following) |
| `docker compose down` | Stop everything; **data is kept** |
| `docker compose down -v` | ⚠️ Stop everything **and erase the database** |

## Using the app

- **Sync now** fetches only games you've played since your last sync, so it's quick.
- **Full re-sync** re-checks every game. Use it after changing your Steam privacy settings, or if numbers look wrong.
- You can sync the same profile **once every 10 minutes**, and the server runs at most 2 syncs at a time.
- **☆ Hunt** (on Near completion) adds a game to your Hunting page. **Refresh** on a hunted game re-syncs just that game.
- **Trending toward 100%** builds up from daily snapshots, so it needs at least two days of data before anything shows.
- If Steam refuses to share a profile's achievements, the sync stops and says so, rather than showing zeros.

## Development setup

For working on the code with instant reloads. This uses its own **SQLite** database (`data/app.db`), separate from Docker's.

You need **Python 3.13** and **Node.js 24**.

**1. Settings:** create `.env` as in the quick start. For development, also keep `PUBLIC_URL=http://localhost:5173` (it's in the template).

**2. Backend** (first terminal, from the repo root):
```bash
python -m venv .venv
```
```bash
source .venv/Scripts/activate
```
(On macOS/Linux: `source .venv/bin/activate`.)
```bash
cd backend
```
```bash
pip install -e ".[dev]"
```
```bash
alembic upgrade head
```
```bash
fastapi dev app/main.py
```
The API runs at http://127.0.0.1:8000, with interactive docs at http://127.0.0.1:8000/docs.

**3. Frontend** (second terminal):
```bash
cd frontend
```
```bash
npm install
```
```bash
npm run dev
```
Open **http://localhost:5173**. Vite passes `/api` requests to the backend.

**4. Commit checks** (once, from the repo root, with the venv active):
```bash
pre-commit install
```

## Configuration (`.env`)

| Setting | Needed for | Notes |
|---|---|---|
| `STEAM_API_KEY` | everything | From [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey). Keep it secret. |
| `SECRET_KEY` | sign-in | Signs the login cookie. A long random value; changing it signs everyone out. |
| `POSTGRES_PASSWORD` | Docker | Database password. Docker refuses to start without it. Use hex characters (from `token_hex`). |
| `PUBLIC_URL` | sign-in | Where the site is reached; Steam sends signed-in users back here. Dev: `http://localhost:5173`. Docker sets `http://localhost:8080` itself. Live: `https://your-domain`. |
| `STEAM_ID` | command line only | Your 17-digit SteamID, used as the default for `python -m app.sync` |
| `CLOUDFLARE_TUNNEL_TOKEN` | live server only | See [Deploying to a server](#deploying-to-a-server) |
| `COMPOSE_FILE` | live server only | `compose.yaml:compose.prod.yaml`, so plain `docker compose` uses the production settings |
| `DAILY_JOB_HOUR_UTC` | optional | Hour (0–23, UTC) the scheduler runs the daily job. Default `6`. |
| `DATABASE_URL` | optional | Override the database. Dev default: SQLite at `data/app.db`. |

## Command reference

Run these from `backend/` with the venv active (development). With Docker, put `docker compose exec backend` in front of them, from the repo root.

| Command | What it does |
|---|---|
| `python -m app.sync` | Sync the `STEAM_ID` profile (only changed games) |
| `python -m app.sync --force` | Re-sync every game |
| `python -m app.sync --steam-id 7656…` | Sync a different profile |
| `python -m app.sync --game 1172620` | Sync one game only |
| `python -m app.daily` | Save Steam's top-25 chart and today's rarity snapshots (the scheduler runs this daily) |
| `python -m app.queries` | Print your rarest achievements and stats to the terminal |

Example with Docker:
```bash
docker compose exec backend python -m app.sync --force --steam-id 76561197960287930
```

## Tests and code quality

**Backend** (from `backend/`):
```bash
pytest
```
```bash
ruff check . && ruff format --check .
```

Tests use a temporary SQLite database and a fake Steam (respx), so they never touch real data or use your API key. To also run them against **Postgres**, start a throwaway one:
```bash
docker run -d --name pgtest -e POSTGRES_USER=showcase -e POSTGRES_PASSWORD=testpw -e POSTGRES_DB=showcase_test -p 5433:5432 postgres:18-alpine
```
```bash
TEST_DATABASE_URL=postgresql+psycopg://showcase:testpw@localhost:5433/showcase_test pytest
```
```bash
docker rm -f pgtest
```

**Frontend** (from `frontend/`):
```bash
npm test && npm run lint && npm run format:check && npm run build
```
`npm run format` fixes formatting automatically.

**On every commit**, pre-commit runs: whitespace and end-of-file fixes, YAML/TOML checks, large-file and private-key checks, Ruff, and **gitleaks** (blocks commits containing secrets).

**On every push and pull request**, GitHub Actions runs:
- **backend:** lint, format, migrations checked on Postgres, tests on SQLite **and** Postgres
- **frontend:** lint, format, tests, type-check and build
- **docker:** builds every image

**Dependabot** opens weekly pull requests for package, Docker image and GitHub Actions updates.

## Changing the database

After editing `backend/app/models.py`, from `backend/`:
```bash
alembic revision --autogenerate -m "describe the change"
```
```bash
ruff check . --fix
```
```bash
alembic upgrade head
```

Read the new file in `alembic/versions/` before committing. Docker applies migrations automatically when the backend starts. CI fails if a model change has no migration (`alembic check`).

## Backups

**Back up** the Docker database to a file (from the repo root):
```bash
docker compose exec -T db pg_dump -U showcase -d showcase --clean --if-exists > backup.sql
```

**Restore** it:
```bash
docker compose exec -T db psql -U showcase -d showcase -q < backup.sql
```

`backup*.sql` and `backups/` are ignored by Git, because they contain user data. On the live server, a `backup` container saves a compressed backup every night into `backups/` and keeps 14 days. Copy those off the server regularly.

## Deploying to a server

The live setup is the same Docker setup, plus `compose.prod.yaml`:
- **Cloudflare Tunnel:** the server makes an outgoing connection to Cloudflare, so no ports are opened and HTTPS is handled by Cloudflare
- **No published ports:** only the tunnel can reach the website container
- **Nightly backups** into `backups/`
- `PUBLIC_URL` is the real `https://` address, which also makes the login cookie HTTPS-only

**Outline** (Ubuntu Server LTS recommended):
1. Install Docker Engine (`curl -fsSL https://get.docker.com | sudo sh`), turn on automatic security updates, and allow only SSH through the firewall (`sudo ufw allow OpenSSH && sudo ufw enable`).
2. In the Cloudflare dashboard: add your domain, then **Networking → Tunnels → Create a tunnel**. Choose Docker and copy only the **token**.
3. On the server, clone the repo and create `.env` with **new** secrets:
   ```
   COMPOSE_FILE=compose.yaml:compose.prod.yaml
   STEAM_API_KEY=...
   SECRET_KEY=...
   POSTGRES_PASSWORD=...
   PUBLIC_URL=https://your-domain.com
   CLOUDFLARE_TUNNEL_TOKEN=...
   ```
   Then `chmod 600 .env`.
4. `docker compose up -d --build`. `docker compose ps` should show six containers: db, backend, scheduler, frontend, tunnel and backup.
5. In Cloudflare, open your tunnel's **Routes → Add route → Published application**: your domain, Service URL **`http://frontend:80`**.
6. Turn on **SSL/TLS → Edge Certificates → Always Use HTTPS**, and add an uptime monitor for `https://your-domain.com/api/health`.

**Updating the live site:**
```bash
git pull && docker compose up -d --build
```

## Security

- **Secrets live only in `.env`** (or the server's), never in code or Git. gitleaks checks every commit.
- **No passwords are handled.** Sign-in uses Steam OpenID: users sign in on Steam's own page, and the server confirms the result with Steam directly.
- **Owner-only changes:** syncing, hunts and deleting data require being signed in as that profile.
- **Abuse limits:** per-visitor request limits in nginx, a 10-minute sync cooldown, and at most 2 syncs at once.
- **Security headers** (Content-Security-Policy and others), a login cookie that is signed, HttpOnly and SameSite=Lax (Secure on HTTPS), and containers that run as non-root.
- **If a secret leaks:** revoke it straight away (Steam key: the same page you created it on; `SECRET_KEY` / `POSTGRES_PASSWORD`: make new ones), then remove it from the code. Deleting a file doesn't remove it from Git history.

## Project structure

```
backend/
  app/
    main.py            the FastAPI app: middleware and routers
    config.py          settings from .env
    database.py        database connection (SQLite or Postgres)
    models.py          database tables
    schemas.py         shapes of the API's JSON
    queries.py         the SQL questions the pages ask
    steam_client.py    every call to Steam's API (with retries)
    steam_login.py     Sign in through Steam (OpenID)
    sync.py            copies a player's Steam data into the database
    sync_jobs.py       tracks syncs running in the background
    charts.py          saves Steam's daily most-played chart
    snapshots.py       saves daily rarity snapshots (for trends)
    daily.py           every daily job, in order
    scheduler.py       runs the daily job once a day
    routers/           API endpoints: auth, players, sync, hunts, overview
  alembic/             database migrations
  tests/               pytest suite (Steam is faked with respx)
frontend/
  src/
    pages/             Overview, Profile, Near completion, Hunting, Privacy
    components/        building blocks (showcase grid, sync panel, ...)
    api/               API client and TypeScript types
    hooks/             data fetching and caching (TanStack Query)
    lib/               small helpers, each with tests
  nginx.conf           web server: routing, rate limits, real visitor IPs
  security-headers.conf
compose.yaml           runs everything locally with Docker
compose.prod.yaml      extra settings for the live server (tunnel, backups)
.github/               CI workflow and Dependabot settings
```

## API reference

Interactive docs: `/docs` on the backend (http://127.0.0.1:8000/docs in development).

| Method | Path | Who | What |
|---|---|---|---|
| GET | `/api/health` | anyone | Is the server up? |
| GET | `/api/overview` | anyone | Most-played chart, trending games |
| GET | `/api/resolve?q=…` | anyone | SteamID from an ID, profile URL or custom name |
| GET | `/api/players/{id}` | anyone | Name, avatar, last synced |
| GET | `/api/players/{id}/showcase` | anyone | Rarest unlocked achievements |
| GET | `/api/players/{id}/in-progress` | anyone | Closest to 100%, easiest missing |
| GET | `/api/players/{id}/stats` | anyone | Totals and unlocks per month |
| GET | `/api/players/{id}/games?status=…&sort=…` | anyone | Every game with completion |
| GET | `/api/players/{id}/hunts` | anyone | Hunted games and their locked achievements |
| POST | `/api/players/{id}/sync?force=…` | owner | Start a sync (background) |
| GET | `/api/players/{id}/sync` | anyone | Sync status |
| PUT / DELETE | `/api/players/{id}/hunts/{appid}` | owner | Start or stop hunting a game |
| POST | `/api/players/{id}/hunts/{appid}/refresh` | owner | Re-sync one hunted game |
| DELETE | `/api/players/{id}` | owner | Delete my data |
| GET | `/api/auth/login`, `/api/auth/callback` | anyone | Sign in through Steam |
| GET | `/api/auth/me` | anyone | Who's signed in (401 if nobody) |
| POST | `/api/auth/logout` | anyone | Sign out |

## Troubleshooting

**Setup**

| Problem | Fix |
|---|---|
| Docker says virtualization is disabled | Turn on **SVM Mode** (AMD) or **Intel VT-x** in your BIOS/UEFI, then restart |
| `failed to connect to the docker API` | Docker Desktop isn't running. Open it and wait for **Engine running**. |
| `required variable POSTGRES_PASSWORD is missing` | Add `POSTGRES_PASSWORD` to `.env` |
| `failed to read dockerfile: open Dockerfile` | The file must be named exactly `Dockerfile`. Capitalization matters. |
| Port 8080 is already in use | Change `"8080:80"` in `compose.yaml` to e.g. `"8081:80"` |
| `python` runs the wrong version, or "module not found" | Activate the venv (`source .venv/Scripts/activate`) and check `python --version` says 3.13 |

**Sign-in and syncing**

| Problem | Fix |
|---|---|
| "STEAM_API_KEY is not set" | Add your key to `.env`, then `docker compose up -d` (Docker) or restart `fastapi dev` |
| "This Steam profile is private" | Set **My profile** to Public in Steam |
| "Steam won't share this profile's achievements" | Set **Game details** to Public in Steam, then click **Full re-sync** |
| Games show but every game has 0 unlocked | Same cause (old data from when Game details was private): make it Public, then **Full re-sync** |
| "Synced recently. You can sync again in N min." | The 10-minute cooldown. Wait, or use the command line. |
| Sync and Hunt buttons are missing | You're not signed in, or you're viewing someone else's profile |
| After signing in you land on the wrong address | `PUBLIC_URL` doesn't match how you open the site (dev 5173, Docker 8080) |
| Sync worked but the page shows old data | Docker (8080) and the dev servers (5173) have **separate databases**. Sync in the one you're viewing. |
| Most played or Trending is empty | Run `python -m app.daily` (the scheduler does it daily in Docker). Trending needs 2+ days of data. |

**Code and Git**

| Problem | Fix |
|---|---|
| Red underlines in VS Code but `npm run build` passes | `Ctrl+Shift+P` → **TypeScript: Restart TS Server** |
| A commit "fails" with "files were modified by this hook" | A hook tidied something. `git add .`, then commit again. |
| `check-yaml` fails on `!reset` | The hook needs `args: [--unsafe]` (already set), because `!reset` is a Docker Compose tag |
| CI fails but everything passes locally | Probably something only on your PC: an unsaved or uncommitted file, or a value from your `.env`. Check `git status`. |

## Working on the code

1. Start from an up-to-date `main`: `git switch main && git pull`
2. Make a branch: `git switch -c short-description`
3. Make your changes, then run the checks under [Tests and code quality](#tests-and-code-quality).
4. `git add .`, then check `git status`: everything you changed should be listed, and `.env` never.
5. `git commit -m "…"`. Look for the `[branch-name abc1234]` line. If a hook changed files, `git add .` and commit again.
6. `git push -u origin short-description`, open a pull request, and merge once CI is green.

## License

MIT. See [LICENSE](LICENSE).

Not affiliated with Valve. Steam and the Steam logo are trademarks of Valve Corporation. Data provided by Steam.
