"""Steam web API calls"""

import httpx

from app.config import STEAM_API_KEY

BASE_URL = "https://api.steampowered.com"


def steam_get(path, **params):
    params["key"] = STEAM_API_KEY
    response = httpx.get(f"{BASE_URL}/{path}/", params = params, timeout = 20)
    response.raise_for_status()
    return response.json()


def get_player_summary(steam_id):
    data = steam_get("ISteamUser/GetPlayerSummaries/v2", steamids = steam_id)
    return data["response"]["players"][0]


def get_owned_games(steam_id):
    data = steam_get(
        "IPlayerService/GetOwnedGames/v1",
        steamid = steam_id,
        include_appinfo = 1,
        include_played_free_games = 1,
    )
    return data["response"].get("games", [])


def get_player_achievements(steam_id, app_id):
    try:
        data = steam_get(
            "ISteamUserStats/GetPlayerAchievements/v1",
            steamid = steam_id,
            appid = app_id,
            l = "english",
        )
    except httpx.HTTPStatusError:
        return []
    return data["playerstats"].get("achievements", [])


def get_schema(app_id):
    """Names, descriptions and icons for every achievement"""
    data = steam_get("ISteamUserStats/GetSchemaForGame/v2", appid = app_id, l = "english")
    return data["game"].get("availableGameStats", {}).get("achievements", [])


def get_global_percentages(app_id):
    data = steam_get(
        "ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2", gameid = app_id
    )
    achievements = data["achievementpercentages"]["achievements"]
    return {a["name"]: float(a["percent"]) for a in achievements}