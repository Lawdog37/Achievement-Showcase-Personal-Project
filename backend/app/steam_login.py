"""Sign in through Steam (OpenID 2.0).

How it works:
1. We send the browser to Steam's login page, with a "return_to" address.
2. The user signs in ON STEAM'S SITE. We never see their password.
3. Steam sends the browser back to return_to, with a signed message that says
   "this is SteamID 7656...".
4. Anyone could fake that message by typing a URL, so we ask Steam directly
   whether it's genuine before believing it.
"""

import re
from urllib.parse import urlencode

import httpx

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
OPENID_NS = "http://specs.openid.net/auth/2.0"
IDENTIFIER_SELECT = "http://specs.openid.net/auth/2.0/identifier_select"
CLAIMED_ID_RE = re.compile(r"^https://steamcommunity\.com/openid/id/(\d{17})$")


def login_url(return_to, realm):
    """The Steam page to send the browser to."""
    params = {
        "openid.ns": OPENID_NS,
        "openid.mode": "checkid_setup",
        "openid.return_to": return_to,
        "openid.realm": realm,
        "openid.identity": IDENTIFIER_SELECT,
        "openid.claimed_id": IDENTIFIER_SELECT,
    }
    return f"{STEAM_OPENID_URL}?{urlencode(params)}"


def verify(params, expected_return_to):
    """Return the SteamID if Steam confirms this sign-in is genuine, otherwise None."""
    openid = {key: value for key, value in params.items() if key.startswith("openid.")}

    # Cheap checks first: is this even a Steam sign-in meant for us?
    if openid.get("openid.mode") != "id_res":
        return None
    if openid.get("openid.op_endpoint") != STEAM_OPENID_URL:
        return None
    if openid.get("openid.return_to") != expected_return_to:
        return None
    match = CLAIMED_ID_RE.match(openid.get("openid.claimed_id", ""))
    if not match:
        return None

    # Then ask Steam: "did you really send this?"
    try:
        response = httpx.post(
            STEAM_OPENID_URL,
            data={**openid, "openid.mode": "check_authentication"},
            timeout=10,
        )
    except httpx.HTTPError:
        return None
    if "is_valid:true" not in response.text.splitlines():
        return None
    return match.group(1)
