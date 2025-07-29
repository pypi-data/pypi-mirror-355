"""
Utility functions for common Puck Bridge operations.
"""

from typing import List, Dict, Any, Optional
from .server import get_game_state, get_event_system, is_connected as server_is_connected
from .game_state import Player, GameState


def get_all_players() -> Dict[int, Player]:
    """Get all currently tracked players"""
    game_state = get_game_state()
    return game_state.players if game_state else {}


def get_player_by_username(username: str) -> Optional[Player]:
    """Find a player by their username"""
    players = get_all_players()
    for player in players.values():
        if player.username.lower() == username.lower():
            return player
    return None


def get_player_by_id(client_id: int) -> Optional[Player]:
    """Get a player by their client ID"""
    players = get_all_players()
    return players.get(client_id)


def get_team_players(team: str) -> List[Player]:
    """Get all players on a specific team"""
    game_state = get_game_state()
    if not game_state:
        return []
    team_dict = game_state.get_players_by_team(team)
    return list(team_dict.values())


def get_blue_players() -> List[Player]:
    """Get all players on the blue team"""
    return get_team_players("blue")


def get_red_players() -> List[Player]:
    """Get all players on the red team"""
    return get_team_players("red")


def get_current_score() -> Dict[str, int]:
    """Get the current game score"""
    game_state = get_game_state()
    if not game_state:
        return {"blue": 0, "red": 0}
    return {"blue": game_state.game_state.blue_score, "red": game_state.game_state.red_score}


def get_game_phase() -> str:
    """Get the current game phase"""
    game_state = get_game_state()
    return game_state.game_state.phase if game_state else "unknown"


def get_game_time() -> float:
    """Get the current game time"""
    game_state = get_game_state()
    return game_state.game_state.time if game_state else 0.0


def get_current_period() -> int:
    """Get the current game period"""
    game_state = get_game_state()
    return game_state.game_state.period if game_state else 0


def is_game_in_progress() -> bool:
    """Check if a game is currently in progress"""
    phase = get_game_phase()
    return phase.lower() in ["playing", "faceoff", "bluescore", "redscore", "replay"]


def is_game_paused() -> bool:
    """Check if the game is currently paused (during warmup or between periods)"""
    phase = get_game_phase()
    return phase.lower() in ["warmup", "periodover"]


def is_game_active() -> bool:
    """Check if a game is active (not in None or GameOver state)"""
    phase = get_game_phase()
    return phase.lower() not in ["none", "gameover"]


def is_period_over() -> bool:
    """Check if the current period is over"""
    return get_game_phase().lower() == "periodover"


def is_game_over() -> bool:
    """Check if the game is completely finished"""
    return get_game_phase().lower() == "gameover"


def is_warmup() -> bool:
    """Check if the game is in warmup phase"""
    return get_game_phase().lower() == "warmup"


def is_scoring_phase() -> bool:
    """Check if currently in a scoring celebration phase"""
    phase = get_game_phase()
    return phase.lower() in ["bluescore", "redscore"]


def get_player_count() -> int:
    """Get the total number of players"""
    return len(get_all_players())


def get_team_balance() -> Dict[str, int]:
    """Get the number of players on each team"""
    return {
        "blue": len(get_blue_players()),
        "red": len(get_red_players()),
        "spectators": len([p for p in get_all_players().values() if p.team.lower() not in ["blue", "red"]]),
    }


def get_top_scorers(limit: int = 5) -> List[Player]:
    """Get the top scoring players"""
    players = list(get_all_players().values())
    return sorted(players, key=lambda p: p.goals, reverse=True)[:limit]


def get_performance_stats() -> Dict[str, float]:
    """Get current performance statistics"""
    game_state = get_game_state()
    if not game_state:
        return {"current_fps": 0.0, "average_fps": 0.0, "min_fps": 0.0, "max_fps": 0.0}

    perf = game_state.performance
    return {
        "current_fps": perf.current_fps,
        "average_fps": perf.average_fps,
        "min_fps": perf.min_fps,
        "max_fps": perf.max_fps,
    }


def format_game_time(time_seconds: float) -> str:
    """Format game time into MM:SS format"""
    minutes = int(time_seconds // 60)
    seconds = int(time_seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def format_score_string() -> str:
    """Get a formatted score string"""
    score = get_current_score()
    return f"Blue {score['blue']} - Red {score['red']}"


def register_goal_handler(handler):
    """Convenience function to register a goal event handler"""
    from .server import register_message_handler

    register_message_handler("goal_scored", handler)


def register_player_join_handler(handler):
    """Convenience function to register a player join handler"""
    from .server import register_message_handler

    register_message_handler("player_spawned", handler)


def register_player_leave_handler(handler):
    """Convenience function to register a player leave handler"""
    from .server import register_message_handler

    register_message_handler("player_despawned", handler)


def register_game_state_handler(handler):
    """Convenience function to register a game state change handler"""
    from .server import register_message_handler

    register_message_handler("game_state", handler)


def is_connected() -> bool:
    """Check if connected to the game server"""
    return server_is_connected()


def get_player_steam_ids() -> Dict[str, str]:
    """Get a mapping of usernames to Steam IDs for all players"""
    players = get_all_players()
    return {player.username: player.steam_id for player in players.values() if player.steam_id}


def find_players_by_partial_name(partial_name: str) -> List[Player]:
    """Find players whose usernames contain the partial name (case insensitive)"""
    players = get_all_players()
    partial_lower = partial_name.lower()
    return [player for player in players.values() if partial_lower in player.username.lower()]
