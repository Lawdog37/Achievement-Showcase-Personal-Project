"""Tests for signing in through Steam, and for who may change what."""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from app import sync_jobs
from app.database import SessionLocal
from app.models import Player
from app.steam_login import STEAM_OPENID_URL
from app.sync import now_utc, sync_player
from tests.fake_steam import PLAYER_ID, setup_basic_library

OTHER_PLAYER = "76561190000000002"


def start_login(client):
    """Click "Sign in": returns the return_to address our app gave Steam."""
    response = client.get("/api/auth/login", follow_redirects=False)
    assert response.status_code == 302
    steam_page = urlparse(response.headers["location"])
    assert steam_page.netloc == "steamcommunity.com"
    return parse_qs(steam_page.query)["openid.return_to"][0]


def steam_sends_back(return_to, steam_id=PLAYER_ID, **changes):
    """What Steam adds to the URL when it sends the browser back to us."""
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "id_res",
        "openid.op_endpoint": STEAM_OPENID_URL,
        "openid.claimed_id": f"https://steamcommunity.com/openid/id/{steam_id}",
        "openid.identity": f"https://steamcommunity.com/openid/id/{steam_id}",
        "openid.return_to": return_to,
        "openid.response_nonce": "2026-10-24T12:00:00Zabc",
        "openid.assoc_handle": "1234567890",
        "openid.signed": "signed,op_endpoint,claimed_id,identity,return_to,response_nonce",
        "openid.sig": "fake-signature",
    }
    params.update(changes)
    params["state"] = parse_qs(urlparse(return_to).query)["state"][0]
    return params


def steam_says(steam, valid):
    return steam.post(STEAM_OPENID_URL).respond(
        text=f"ns:http://specs.openid.net/auth/2.0\nis_valid:{'true' if valid else 'false'}\n"
    )


def test_nobody_is_signed_in_at_first(client):
    assert client.get("/api/auth/me").status_code == 401


def test_sign_in_through_steam(client, steam):
    steam_says(steam, valid=True)
    return_to = start_login(client)

    response = client.get(
        "/api/auth/callback", params=steam_sends_back(return_to), follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == f"/player/{PLAYER_ID}"
    assert client.get("/api/auth/me").json() == {"steam_id": PLAYER_ID}


def test_sign_out(client, steam):
    steam_says(steam, valid=True)
    return_to = start_login(client)
    client.get("/api/auth/callback", params=steam_sends_back(return_to), follow_redirects=False)

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_steam_rejects_a_fake_sign_in(client, steam):
    steam_says(steam, valid=False)
    return_to = start_login(client)

    response = client.get("/api/auth/callback", params=steam_sends_back(return_to))

    assert response.status_code == 400
    assert client.get("/api/auth/me").status_code == 401


def test_sign_in_that_did_not_start_here_is_rejected(client, steam):
    route = steam_says(steam, valid=True)
    return_to = start_login(client)
    params = steam_sends_back(return_to)
    params["state"] = "made-up"

    assert client.get("/api/auth/callback", params=params).status_code == 400
    assert not route.called  # rejected before even asking Steam


def test_sign_in_meant_for_another_site_is_rejected(client, steam):
    route = steam_says(steam, valid=True)
    return_to = start_login(client)
    params = steam_sends_back(
        return_to, **{"openid.return_to": "https://evil.example/api/auth/callback"}
    )

    assert client.get("/api/auth/callback", params=params).status_code == 400
    assert not route.called


def test_identity_from_another_provider_is_rejected(client, steam):
    steam_says(steam, valid=True)
    return_to = start_login(client)
    params = steam_sends_back(
        return_to, **{"openid.claimed_id": f"https://evil.example/openid/id/{PLAYER_ID}"}
    )

    assert client.get("/api/auth/callback", params=params).status_code == 400


# --- Who may change what --------------------------------------------------
@pytest.fixture
def library(steam):
    setup_basic_library(steam)
    sync_player(PLAYER_ID)


def test_hunting_needs_sign_in(client, library):
    assert client.put(f"/api/players/{PLAYER_ID}/hunts/10").status_code == 401


def test_you_cannot_change_someone_elses_hunts(client, library):
    from app.deps import current_user_id
    from app.main import app

    app.dependency_overrides[current_user_id] = lambda: OTHER_PLAYER
    assert client.put(f"/api/players/{PLAYER_ID}/hunts/10").status_code == 403


def test_reading_stays_public(client, library):
    assert client.get(f"/api/players/{PLAYER_ID}/hunts").status_code == 200
    assert client.get(f"/api/players/{PLAYER_ID}/showcase").status_code == 200


def test_syncing_needs_sign_in(client):
    assert client.post(f"/api/players/{PLAYER_ID}/sync").status_code == 401


def test_sync_cooldown(client, library, signed_in):
    # The library fixture just synced, so it's too soon to sync again
    response = client.post(f"/api/players/{PLAYER_ID}/sync")
    assert response.status_code == 429
    assert "10 min" in response.json()["detail"]

    # Pretend the last sync was 11 minutes ago
    with SessionLocal() as session:
        session.get(Player, PLAYER_ID).last_synced_at = now_utc() - timedelta(minutes=11)
        session.commit()
    assert client.post(f"/api/players/{PLAYER_ID}/sync").status_code == 202


def test_only_two_syncs_at_once(client, signed_in):
    sync_jobs.try_start("76561190000000098")
    sync_jobs.try_start("76561190000000099")

    response = client.post(f"/api/players/{PLAYER_ID}/sync")

    assert response.status_code == 503
