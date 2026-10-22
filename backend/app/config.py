"""All settings come from environment variables"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # searches upward from this file and finds the repo's .env

# Repo root = two folders up from this file (backend/app/config.py)
REPO_ROOT = Path(__file__).resolve().parents[2]

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID = os.getenv("STEAM_ID")

DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(exist_ok = True)  # SQLite creates the file, but not the folder

DEFAULT_DB = (DATA_DIR / "app.db").as_posix()
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB}")