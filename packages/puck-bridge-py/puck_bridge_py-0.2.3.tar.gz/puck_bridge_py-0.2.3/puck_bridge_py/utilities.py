"""
Utility functions for common Puck Bridge operations.
"""

from typing import List, Dict, Optional
from .game_state import Player


class Utilities:
    """Utilities class that works with a specific PuckBridge instance"""

    def __init__(self, bridge):
        self.bridge = bridge

    def get_all_players(self) -> Dict[int, Player]:
        """Get all currently tracked players"""
        game_state = self.bridge.get_game_state()
        return game_state.players if game_state else {}

    def get_player_by_username(self, username: str) -> Optional[Player]:
        """Find a player by their username"""
        players = self.get_all_players()
        for player in players.values():
            if player.username.lower() == username.lower():
                return player
        return None

    def get_player_by_id(self, client_id: int) -> Optional[Player]:
        """Get a player by their client ID"""
        players = self.get_all_players()
        return players.get(client_id)

    def get_team_players(self, team: str) -> List[Player]:
        """Get all players on a specific team"""
        game_state = self.bridge.get_game_state()
        if not game_state:
            return []
        team_dict = game_state.get_players_by_team(team)
        return list(team_dict.values())

    def get_blue_players(self) -> List[Player]:
        """Get all players on the blue team"""
        return self.get_team_players("blue")

    def get_red_players(self) -> List[Player]:
        """Get all players on the red team"""
        return self.get_team_players("red")

    def get_current_score(self) -> Dict[str, int]:
        """Get the current game score"""
        game_state = self.bridge.get_game_state()
        if not game_state:
            return {"blue": 0, "red": 0}
        return {"blue": game_state.game_state.blue_score, "red": game_state.game_state.red_score}

    def get_game_phase(self) -> str:
        """Get the current game phase"""
        game_state = self.bridge.get_game_state()
        return game_state.game_state.phase if game_state else "unknown"

    def get_game_time(self) -> float:
        """Get the current game time"""
        game_state = self.bridge.get_game_state()
        return game_state.game_state.time if game_state else 0.0

    def get_current_period(self) -> int:
        """Get the current game period"""
        game_state = self.bridge.get_game_state()
        return game_state.game_state.period if game_state else 0

    def is_game_in_progress(self) -> bool:
        """Check if a game is currently in progress"""
        phase = self.get_game_phase()
        return phase.lower() in ["playing", "faceoff", "bluescore", "redscore", "replay"]

    def is_game_paused(self) -> bool:
        """Check if the game is currently paused (during warmup or between periods)"""
        phase = self.get_game_phase()
        return phase.lower() in ["warmup", "periodover"]

    def is_game_active(self) -> bool:
        """Check if a game is active (not in None or GameOver state)"""
        phase = self.get_game_phase()
        return phase.lower() not in ["none", "gameover"]

    def is_period_over(self) -> bool:
        """Check if the current period is over"""
        return self.get_game_phase().lower() == "periodover"

    def is_game_over(self) -> bool:
        """Check if the game is completely finished"""
        return self.get_game_phase().lower() == "gameover"

    def is_warmup(self) -> bool:
        """Check if the game is in warmup phase"""
        return self.get_game_phase().lower() == "warmup"

    def is_scoring_phase(self) -> bool:
        """Check if currently in a scoring celebration phase"""
        phase = self.get_game_phase()
        return phase.lower() in ["bluescore", "redscore"]

    def get_player_count(self) -> int:
        """Get the total number of players"""
        return len(self.get_all_players())

    def get_team_balance(self) -> Dict[str, int]:
        """Get the number of players on each team"""
        return {
            "blue": len(self.get_blue_players()),
            "red": len(self.get_red_players()),
            "spectators": len([p for p in self.get_all_players().values() if p.team.lower() not in ["blue", "red"]]),
        }

    def get_top_scorers(self, limit: int = 5) -> List[Player]:
        """Get the top scoring players"""
        players = list(self.get_all_players().values())
        return sorted(players, key=lambda p: p.goals, reverse=True)[:limit]

    def get_performance_stats(self) -> Dict[str, float]:
        """Get current performance statistics"""
        game_state = self.bridge.get_game_state()
        if not game_state:
            return {"current_fps": 0.0, "average_fps": 0.0, "min_fps": 0.0, "max_fps": 0.0}

        perf = game_state.performance
        return {
            "current_fps": perf.current_fps,
            "average_fps": perf.average_fps,
            "min_fps": perf.min_fps,
            "max_fps": perf.max_fps,
        }

    def format_game_time(self, time_seconds: float) -> str:
        """Format game time into MM:SS format"""
        minutes = int(time_seconds // 60)
        seconds = int(time_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def format_score_string(self) -> str:
        """Get a formatted score string"""
        score = self.get_current_score()
        return f"Blue {score['blue']} - Red {score['red']}"

    def register_goal_handler(self, handler):
        """Convenience function to register a goal event handler"""
        self.bridge.register_message_handler("goal_scored", handler)

    def register_player_join_handler(self, handler):
        """Convenience function to register a player join handler"""
        self.bridge.register_message_handler("player_spawned", handler)

    def register_player_leave_handler(self, handler):
        """Convenience function to register a player leave handler"""
        self.bridge.register_message_handler("player_despawned", handler)

    def register_game_state_handler(self, handler):
        """Convenience function to register a game state change handler"""
        self.bridge.register_message_handler("game_state", handler)

    def is_connected(self) -> bool:
        """Check if connected to the game server"""
        return self.bridge.is_connected()

    def register_full_state_handler(self, handler):
        """
        Register a handler that receives the complete game state whenever anything changes.

        The handler will be called with a dictionary containing:
        - game_state: Current game phase, time, period, scores
        - players: Dictionary of all players by client_id
        - performance: Current FPS and performance metrics
        - summary: High-level game summary

        Args:
            handler: Function that accepts (state_dict) as parameter
        """

        def full_state_wrapper(message_type, data):
            full_state = self.get_complete_game_state()
            full_state["message_type"] = message_type
            handler(full_state)

        # Register for all message types that could change game state
        state_changing_messages = [
            "game_state",
            "player_spawned",
            "player_despawned",
            "player_updated",
            "goal_scored",
            "performance_update",
        ]

        for msg_type in state_changing_messages:
            self.bridge.register_message_handler(msg_type, lambda mt=msg_type, d=None: full_state_wrapper(mt, d))

    def get_complete_game_state(self) -> dict:
        """Get the complete current game state as a dictionary"""
        game_state = self.bridge.get_game_state()
        if not game_state:
            return {"game_state": None, "players": {}, "performance": None, "summary": None, "connected": False}

        return {
            "game_state": {
                "phase": game_state.game_state.phase,
                "time": game_state.game_state.time,
                "period": game_state.game_state.period,
                "blue_score": game_state.game_state.blue_score,
                "red_score": game_state.game_state.red_score,
                "last_updated": game_state.game_state.last_updated.isoformat(),
            },
            "players": {
                str(client_id): {
                    "client_id": player.client_id,
                    "username": player.username,
                    "state": player.state,
                    "team": player.team,
                    "role": player.role,
                    "number": player.number,
                    "goals": player.goals,
                    "assists": player.assists,
                    "ping": player.ping,
                    "handedness": player.handedness,
                    "country": player.country,
                    "steam_id": player.steam_id,
                    "patreon_level": player.patreon_level,
                    "admin_level": player.admin_level,
                    "last_updated": player.last_updated.isoformat(),
                }
                for client_id, player in game_state.players.items()
            },
            "performance": {
                "current_fps": game_state.performance.current_fps,
                "average_fps": game_state.performance.average_fps,
                "min_fps": game_state.performance.min_fps,
                "max_fps": game_state.performance.max_fps,
                "last_updated": game_state.performance.last_updated.isoformat(),
            },
            "summary": game_state.get_game_summary(),
            "connected": self.is_connected(),
        }
