"""All settings come from environment variables"""

import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # searches upward from this file and finds the repo's .env

# Repo root = two folders up from this file (backend/app/config.py)
REPO_ROOT = Path(__file__).resolve().parents[2]

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID = os.getenv("STEAM_ID")

DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)  # SQLite creates the file, but not the folder

DEFAULT_DB = (DATA_DIR / "app.db").as_posix()
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB}")

# The address people use to reach the site. Steam sends signed-in users back here.
# Dev servers: http://localhost:5173. Docker: http://localhost:8080. Online: https://yoursite
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:5173").rstrip("/")

# Signs the login cookie. Anyone who knows it could pretend to be any user,
# so it lives only in .env (or the host's secret settings), never in code.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(32)
    logging.getLogger(__name__).warning(
        "SECRET_KEY is not set, so a random one is used and everyone is signed out "
        "whenever the server restarts. Add SECRET_KEY to your .env file."
    )
