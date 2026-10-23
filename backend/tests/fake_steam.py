"""Helpers that teach the fake Steam API (respx) what to answer."""

PLAYER_ID = "76561190000000001"
NOW = 1_750_000_000  # a fixed time in the past (June 2025) as a Unix timestamp


def add_profile(steam, visibility=3, name="Test Player"):
    steam.get("/ISteamUser/GetPlayerSummaries/v2/").respond(
        json={
            "response": {
                "players": [
                    {
                        "steamid": PLAYER_ID,
                        "personaname": name,
                        "avatarfull": "https://example.com/avatar.jpg",
                        "communityvisibilitystate": visibility,
                    }
                ]
            }
        }
    )


def add_owned_games(steam, games):
    """games: list of (app_id, name, playtime_minutes, last_played_unix)"""
    steam.get("/IPlayerService/GetOwnedGames/v1/").respond(
        json={
            "response": {
                "game_count": len(games),
                "games": [
                    {
                        "appid": app_id,
                        "name": name,
                        "playtime_forever": playtime,
                        "rtime_last_played": last_played,
                        "img_icon_url": "abc123",
                    }
                    for app_id, name, playtime, last_played in games
                ],
            }
        }
    )


def add_game_achievements(steam, app_id, achievements):
    """achievements: list of (api_name, global_percent, unlocked: bool)"""
    steam.get("/ISteamUserStats/GetSchemaForGame/v2/", params={"appid": app_id}).respond(
        json={
            "game": {
                "availableGameStats": {
                    "achievements": [
                        {
                            "name": api_name,
                            "displayName": api_name.title(),
                            "description": f"Do the {api_name} thing",
                            "hidden": 0,
                            "icon": f"https://example.com/{api_name}.jpg",
                            "icongray": f"https://example.com/{api_name}_gray.jpg",
                        }
                        for api_name, _, _ in achievements
                    ]
                }
            }
        }
    )
    steam.get(
        "/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/", params={"gameid": app_id}
    ).respond(
        json={
            "achievementpercentages": {
                # Steam really does send percent as text
                "achievements": [{"name": n, "percent": str(p)} for n, p, _ in achievements]
            }
        }
    )
    steam.get("/ISteamUserStats/GetPlayerAchievements/v1/", params={"appid": app_id}).respond(
        json={
            "playerstats": {
                "success": True,
                "achievements": [
                    {
                        "apiname": api_name,
                        "achieved": 1 if unlocked else 0,
                        "unlocktime": NOW - 86_400 if unlocked else 0,
                    }
                    for api_name, _, unlocked in achievements
                ],
            }
        }
    )


def add_game_without_achievements(steam, app_id):
    steam.get("/ISteamUserStats/GetSchemaForGame/v2/", params={"appid": app_id}).respond(
        json={"game": {}}
    )


def setup_basic_library(steam):
    """A small library: one game with achievements, one without, one unplayed."""
    add_profile(steam)
    add_owned_games(
        steam,
        [
            (10, "Rare Game", 600, NOW - 3_600),
            (20, "No Achievements Game", 120, NOW - 7_200),
            (30, "Never Played", 0, 0),
        ],
    )
    add_game_achievements(
        steam,
        10,
        [
            ("LEGEND", 0.4, True),
            ("VETERAN", 12.5, True),
            ("TUTORIAL", 91.0, False),
        ],
    )
    add_game_without_achievements(steam, 20)
    add_game_without_achievements(steam, 30)  # only asked for when forcing a sync
