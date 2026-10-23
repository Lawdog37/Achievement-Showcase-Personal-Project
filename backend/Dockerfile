# The recipe for the backend container: Python + FastAPI + the database tools.
FROM python:3.13-slim

# uv installs Python packages much faster than pip
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv

WORKDIR /app

# 1) Install dependencies first. Docker caches each step, so this slow step
#    only re-runs when pyproject.toml changes, not on every code change.
COPY pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml

# 2) Then copy the code
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# Don't run as root: if the app were ever hacked, the damage stays contained.
# /data is where the SQLite database lives (a Docker volume is mounted there).
RUN useradd --create-home appuser && mkdir /data && chown appuser /data
USER appuser

ENV DATABASE_URL=sqlite:////data/app.db \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# On every start: bring the database up to date, then start the API
CMD ["sh", "-c", "alembic upgrade head && fastapi run app/main.py --port 8000"]
