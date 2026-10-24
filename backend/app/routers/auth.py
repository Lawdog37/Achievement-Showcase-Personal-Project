"""Sign in, see who's signed in, sign out."""

import secrets

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app import steam_login
from app.config import PUBLIC_URL
from app.deps import CurrentUserId
from app.schemas import MeOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def callback_url(state):
    return f"{PUBLIC_URL}/api/auth/callback?state={state}"


@router.get("/login")
def login(request: Request):
    """Send the browser to Steam's sign-in page."""
    # A random one-time code, remembered in this browser's cookie. Steam hands
    # it back to us, which proves the sign-in started here and not on another site.
    state = secrets.token_urlsafe(16)
    request.session["login_state"] = state
    return RedirectResponse(steam_login.login_url(callback_url(state), PUBLIC_URL), 302)


@router.get("/callback")
def callback(request: Request, state: str = ""):
    """Steam sends the browser back here after signing in."""
    expected = request.session.pop("login_state", None)
    if not expected or not secrets.compare_digest(state, expected):
        raise HTTPException(400, "This sign-in expired or didn't start here. Please try again.")

    steam_id = steam_login.verify(dict(request.query_params), callback_url(expected))
    if steam_id is None:
        raise HTTPException(400, "Steam couldn't confirm your sign-in. Please try again.")

    request.session.clear()  # start a fresh session for the signed-in user
    request.session["steam_id"] = steam_id
    return RedirectResponse(f"/player/{steam_id}", 302)


@router.get("/me", response_model=MeOut)
def me(user_id: CurrentUserId):
    """Who is signed in? 401 if nobody."""
    if user_id is None:
        raise HTTPException(401, "Not signed in")
    return {"steam_id": user_id}


@router.post("/logout", status_code=204)
def logout(request: Request):
    request.session.clear()
