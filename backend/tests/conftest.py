"""Shared test setup. pytest loads this file automatically before any test.

Tests must never touch your real database or call the real Steam API, so:
- the app is pointed at a throwaway database in a temp folder
- the API key is a fake one
- every Steam request is answered by respx (a fake Steam) instead
"""

import os
import tempfile
import time
from pathlib import Path

# These must be set BEFORE the app is imported, because app/config.py reads
# them on import. (load_dotenv never overrides variables that already exist.)
_temp_dir = Path(tempfile.mkdtemp())
os.environ["DATABASE_URL"] = f"sqlite:///{(_temp_dir / 'test.db').as_posix()}"
os.environ["STEAM_API_KEY"] = "fake-test-key"

import pytest  # noqa: E402
import respx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_database():
    """Every test starts with empty tables."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    """Skip the polite delays and retry waits so tests run instantly."""
    monkeypatch.setattr("app.sync.DELAY_BETWEEN_GAMES", 0)
    monkeypatch.setattr(time, "sleep", lambda seconds: None)


@pytest.fixture
def steam():
    """A fake Steam API. Any request a test didn't set up fails loudly."""
    with respx.mock(base_url="https://api.steampowered.com", assert_all_called=False) as mock:
        yield mock


@pytest.fixture
def client():
    """Calls our FastAPI app in-process, no server needed."""
    return TestClient(app)
