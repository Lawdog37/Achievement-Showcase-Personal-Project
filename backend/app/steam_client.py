"""Every call to the Steam Web API lives here."""

import logging
import time

import httpx

from app.config import STEAM_API_KEY

logger = logging.getLogger(__name__)

BASE_URL = "https://api.steampowered.com"
MAX_ATTEMPTS = 4
RETRY_STATUSES = {429, 500, 502, 503, 504}  # "slow down" and temporary server errors

# One shared client reuses the same connection for every call (much faster)
client = httpx.Client(base_url=BASE_URL, timeout=20)


class SteamAPIError(Exception):
    """Steam API Call Failed"""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def steam_get(path, **params):
    """Call a Steam endpoint, retrying temporary failures with growing waits"""
    if not STEAM_API_KEY:
        raise SteamAPIError("STEAM_API_KEY is not set. Add it to your .env file.")
    params["key"] = STEAM_API_KEY
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.get(f"/{path}/", params=params)
        except httpx.TransportError as error:  # no internet, timeout, etc.
            problem, status = f"network error ({type(error).__name__})", None
        else:
            if response.status_code not in RETRY_STATUSES:
                if response.is_error:
                    raise SteamAPIError(
                        f"{path} returned HTTP {response.status_code}",
                        response.status_code,
                    )
                return response.json()
            problem, status = f"HTTP {response.status_code}", response.status_code

        if attempt == MAX_ATTEMPTS:
            raise SteamAPIError(f"{path} failed after {attempt} tries: {problem}", status)
        wait = 2**attempt  # 2, 4, 8 seconds ("exponential backoff")
        logger.warning("%s: %s, retrying in %ds", path, problem, wait)
        time.sleep(wait)


def get_player_summary(steam_id):
    """Profile info, or None if no such user exists."""
    data = steam_get("ISteamUser/GetPlayerSummaries/v2", steamids=steam_id)
    players = data["response"]["players"]
    return players[0] if players else None


def get_owned_games(steam_id):
    data = steam_get(
        "IPlayerService/GetOwnedGames/v1",
        steamid=steam_id,
        include_appinfo=1,
        include_played_free_games=1,
    )
    return data["response"].get("games", [])


def get_player_achievements(steam_id, app_id):
    try:
        data = steam_get(
            "ISteamUserStats/GetPlayerAchievements/v1",
            steamid=steam_id,
            appid=app_id,
            l="english",
        )
    except SteamAPIError as error:
        if error.status_code in (400, 403):
            return []
        raise
    return data["playerstats"].get("achievements", [])


def get_schema(app_id):
    """Names, descriptions and icons for every achievement in a game"""
    data = steam_get("ISteamUserStats/GetSchemaForGame/v2", appid=app_id, l="english")
    return data.get("game", {}).get("availableGameStats", {}).get("achievements", [])


def get_global_percentages(app_id):
    data = steam_get("ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2", gameid=app_id)
    achievements = data["achievementpercentages"]["achievements"]
    return {a["name"]: float(a["percent"]) for a in achievements}


def resolve_vanity_url(name):
    """Turn a custom profile name (steamcommunity.com/id/NAME) into SteamID"""
    data = steam_get("ISteamUser/ResolveVanityURL/v1", vanityurl=name)
    response = data["response"]
    return response["steamid"] if response.get("success") == 1 else None


def get_most_played():
    """Steam's daily chart of the 100 most-played games.
    Each entry has: rank, appid, last_week_rank, peak_in_game."""
    data = steam_get("ISteamChartsService/GetMostPlayedGames/v1")
    return data["response"].get("ranks", [])


STORE_URL = "https://store.steampowered.com/api/appdetails"


def get_store_details(app_id):
    """A game's real name and banner image from the Steam Store.
    The Store API isn't officially documented and limits how often you can call
    """
    try:
        response = client.get(STORE_URL, params={"appids": app_id, "filters": "basic"})
        entry = response.json().get(str(app_id), {}) if response.is_success else {}
    except (httpx.HTTPError, ValueError):
        return None
    if not entry.get("success"):
        return None
    data = entry.get("data", {})
    return {"name": data.get("name"), "capsule_url": data.get("capsule_image")}
