"""Phase 1: exploring the Steam Web API and printing your rarest achievements."""
"""This is more of a playground in a sense that this will not be used in the final product"""
import os
import sys
from datetime import datetime

import httpx
from dotenv import load_dotenv

# --- Setup -------------------------------------------------------------
load_dotenv()  # reads .env into environment variables
API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID = os.getenv("STEAM_ID")
BASE_URL = "https://api.steampowered.com"

if not API_KEY or not STEAM_ID:
    sys.exit("Missing STEAM_API_KEY or STEAM_ID in your .env file")


def steam_get(path, **params):
    """Call a Steam Web API endpoint and return the JSON as a dictionary"""
    params["key"] = API_KEY
    response = httpx.get(f"{BASE_URL}/{path}/", params = params, timeout = 20)
    response.raise_for_status()  # turns 4xx/5xx errors into exceptions
    return response.json()


# --- Who am I? -------------------------------------------------
def get_player_summary():
    data = steam_get("ISteamUser/GetPlayerSummaries/v2", steamids = STEAM_ID)
    return data["response"]["players"][0]


# --- What do I own? --------------------------------------------
def get_owned_games():
    data = steam_get(
        "IPlayerService/GetOwnedGames/v1",
        steamid = STEAM_ID,
        include_appinfo = 1,
        include_played_free_games = 1,
    )
    return data["response"].get("games", [])


# --- Achievements for one game ---------------------------------
def get_player_achievements(app_id):
    try:
        data = steam_get(
            "ISteamUserStats/GetPlayerAchievements/v1",
            steamid = STEAM_ID,
            appid = app_id,
            l = "english",
        )
    except httpx.HTTPStatusError:
        return []  # Edge cases(No achievements/steam didnt respond)
    return data["playerstats"].get("achievements", [])


def get_global_percentages(app_id):
    data = steam_get(
        "ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2", gameid=app_id
    )
    achievements = data["achievementpercentages"]["achievements"]
    # Steam sends percent as text like "40.9", so convert it to a number
    return {a["name"]: float(a["percent"]) for a in achievements}


def main():
    player = get_player_summary()
    print(f"Player: {player['personaname']}")

    games = get_owned_games()
    games.sort(key = lambda g: g["playtime_forever"], reverse = True)
    print(f"\nYou own {len(games)} games. Most played:")
    for game in games[:10]:
        hours = game["playtime_forever"] / 60
        print(f"  {game['name']:<40} {hours:>7.1f} h   appid {game['appid']}")

    # Use the appid typed after the script name, or default to most played
    app_id = int(sys.argv[1]) if len(sys.argv) > 1 else games[0]["appid"]
    game_name = next((g["name"] for g in games if g["appid"] == app_id), app_id)

    achievements = get_player_achievements(app_id)
    if not achievements:
        print(f"\n{game_name} has no achievements (or you don't own it).")
        return

    percentages = get_global_percentages(app_id)
    unlocked = [a for a in achievements if a["achieved"] == 1]
    for a in unlocked:
        a["percent"] = percentages.get(a["apiname"], 100.0)
    unlocked.sort(key = lambda a: a["percent"])

    done = len(unlocked) / len(achievements) * 100
    print(f"\n{game_name}: {len(unlocked)}/{len(achievements)} unlocked ({done:.0f}%)")
    print("Your rarest achievements:")
    for a in unlocked[:10]:
        date = datetime.fromtimestamp(a["unlocktime"]).strftime("%Y-%m-%d")
        print(f"  {a['percent']:5.1f}%  {a['name']:<35} unlocked {date}")


if __name__ == "__main__":
    main()