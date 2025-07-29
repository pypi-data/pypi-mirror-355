from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Player:
    client_id: int
    username: str
    state: str = "unknown"
    team: str = "none"
    role: str = "none"
    number: int = 0
    goals: int = 0
    assists: int = 0
    ping: int = 0
    handedness: str = "right"
    country: str = ""
    steam_id: str = ""
    patreon_level: int = 0
    admin_level: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class GameState:
    phase: str = "unknown"
    time: float = 0.0
    period: int = 0
    blue_score: int = 0
    red_score: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class Performance:
    current_fps: float = 0.0
    min_fps: float = 0.0
    average_fps: float = 0.0
    max_fps: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class GameStateManager:
    def __init__(self):
        self.game_state = GameState()
        self.players: Dict[int, Player] = {}
        self.performance = Performance()
        self._last_goal_data: Optional[Dict[str, Any]] = None

    def update_game_state(self, data: Dict[str, Any]):
        """Update the current game state from incoming data"""
        if "phase" in data:
            self.game_state.phase = data["phase"]
        if "time" in data:
            self.game_state.time = data["time"]
        if "period" in data:
            self.game_state.period = data["period"]
        if "scores" in data:
            scores = data["scores"]
            if "blue" in scores:
                self.game_state.blue_score = scores["blue"]
            if "red" in scores:
                self.game_state.red_score = scores["red"]

        self.game_state.last_updated = datetime.now()

    def update_player(self, client_id: int, player_data: Dict[str, Any]):
        """Update or create a player from incoming data"""
        if client_id not in self.players:
            self.players[client_id] = Player(client_id=client_id, username="unknown")

        player = self.players[client_id]

        # Update player fields if they exist in the data
        for field_name in [
            "username",
            "state",
            "team",
            "role",
            "number",
            "goals",
            "assists",
            "ping",
            "handedness",
            "country",
            "steam_id",
            "patreon_level",
            "admin_level",
        ]:
            if field_name in player_data:
                setattr(player, field_name, player_data[field_name])

        player.last_updated = datetime.now()

    def remove_player(self, client_id: int):
        """Remove a player from tracking"""
        if client_id in self.players:
            del self.players[client_id]

    def update_performance(self, perf_data: Dict[str, Any]):
        """Update performance metrics"""
        if "fps" in perf_data:
            fps = perf_data["fps"]
            if "current" in fps:
                self.performance.current_fps = fps["current"]
            if "min" in fps:
                self.performance.min_fps = fps["min"]
            if "average" in fps:
                self.performance.average_fps = fps["average"]
            if "max" in fps:
                self.performance.max_fps = fps["max"]

        self.performance.last_updated = datetime.now()

    def set_last_goal_data(self, goal_data: Dict[str, Any]):
        """Store the last goal data for reference"""
        self._last_goal_data = goal_data

    def get_players_by_team(self, team: str) -> Dict[int, Player]:
        """Get all players on a specific team"""
        return {cid: player for cid, player in self.players.items() if player.team.lower() == team.lower()}

    def get_game_summary(self) -> Dict[str, Any]:
        """Get a summary of the current game state"""
        return {
            "game_state": {
                "phase": self.game_state.phase,
                "time": self.game_state.time,
                "period": self.game_state.period,
                "scores": {"blue": self.game_state.blue_score, "red": self.game_state.red_score},
            },
            "player_count": len(self.players),
            "blue_players": len(self.get_players_by_team("blue")),
            "red_players": len(self.get_players_by_team("red")),
            "performance": {"fps": self.performance.current_fps, "avg_fps": self.performance.average_fps},
        }

    def is_connected(self) -> bool:
        """Check if we have an active connection (recent data or players)"""
        import time

        current_time = time.time()

        # Check if game state was updated recently (within last 30 seconds)
        game_state_age = (
            (current_time - self.game_state.last_updated.timestamp()) if self.game_state.last_updated else float("inf")
        )

        # Check if performance data is recent
        perf_age = (
            (current_time - self.performance.last_updated.timestamp())
            if self.performance.last_updated
            else float("inf")
        )

        # Consider connected if we have recent data or players
        return game_state_age < 30 or perf_age < 30 or len(self.players) > 0

    def get_leading_team(self) -> str:
        """Get the name of the team that's currently leading"""
        if self.game_state.blue_score > self.game_state.red_score:
            return "blue"
        elif self.game_state.red_score > self.game_state.blue_score:
            return "red"
        else:
            return "tied"

    def get_score_difference(self) -> int:
        """Get the absolute score difference between teams"""
        return abs(self.game_state.blue_score - self.game_state.red_score)

    def get_active_players(self) -> Dict[int, Player]:
        """Get players that are actively playing (not spectating)"""
        return {
            cid: player
            for cid, player in self.players.items()
            if player.team.lower() in ["blue", "red"] and player.state != "spectating"
        }

    def find_player_by_name(self, username: str) -> Optional[Player]:
        """Find a player by username (case insensitive)"""
        for player in self.players.values():
            if player.username.lower() == username.lower():
                return player
        return None
