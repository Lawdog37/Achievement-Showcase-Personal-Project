"""The web API. Run it (from the backend folder):  fastapi dev app/main.py"""

import logging

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.config import PUBLIC_URL, SECRET_KEY
from app.routers.auth import router as auth_router
from app.routers.hunts import router as hunts_router
from app.routers.overview import router as overview_router
from app.routers.players import router as players_router
from app.routers.sync import router as sync_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
# httpx logs every URL at INFO level, and our URLs contain the API key
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI(
    title="Achievement Showcase API",
    version="0.1.0",
    description="Steam achievements, rarest first.",
)
# Keeps track of who is signed in, using a cookie signed with SECRET_KEY.
# The browser can store it but can't change it without the signature breaking.
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="showcase_session",
    max_age=30 * 24 * 60 * 60,  # stay signed in for 30 days
    same_site="lax",  # not sent with requests from other sites: blocks CSRF attacks
    https_only=PUBLIC_URL.startswith("https://"),  # online, only send it over HTTPS
)
app.include_router(auth_router)
app.include_router(players_router)
app.include_router(sync_router)
app.include_router(hunts_router)
app.include_router(overview_router)


@app.get("/api/health", tags=["meta"])
def health():
    """A quick 'is the server up?' check. Hosting platforms call this."""
    return {"status": "ok"}
