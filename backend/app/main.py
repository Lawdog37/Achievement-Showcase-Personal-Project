"""The web API. Run it (from the backend folder):  fastapi dev app/main.py"""

import logging

from fastapi import FastAPI

from app.routers.hunts import router as hunts_router
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
app.include_router(players_router)
app.include_router(sync_router)
app.include_router(hunts_router)


@app.get("/api/health", tags=["meta"])
def health():
    """A quick 'is the server up?' check. Hosting platforms call this."""
    return {"status": "ok"}
