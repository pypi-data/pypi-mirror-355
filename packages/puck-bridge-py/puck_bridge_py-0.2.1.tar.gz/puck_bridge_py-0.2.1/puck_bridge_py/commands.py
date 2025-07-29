"""
Command utilities for sending commands to the Puck Bridge server.
"""

import logging
from typing import Optional
from .server import send_command

logger = logging.getLogger(__name__)


class Commands:
    """Commands class that works with a specific PuckBridge instance"""

    def __init__(self, bridge):
        self.bridge = bridge

    def send_system_message(self, message: str) -> bool:
        """Send a system message to all players"""
        if not message:
            logger.warning("Cannot send empty system message")
            return False

        return self.bridge.send_command("system_message", {"message": message})

    def restart_game(
        self, reason: str = "Game restarted by administrator", warmup: bool = True, warmup_time: int = -1
    ) -> bool:
        """Restart the current game"""
        payload = {"reason": reason, "warmup": warmup}

        if warmup_time > 0:
            payload["warmup_time"] = warmup_time

        return self.bridge.send_command("restart_game", payload)

    def kick_player(self, steam_id: str, reason: str = "Kicked by administrator", apply_timeout: bool = True) -> bool:
        """Kick a player by their Steam ID"""
        if not steam_id:
            logger.warning("Cannot kick player: Steam ID is required")
            return False

        return self.bridge.send_command(
            "kick_player", {"steamid": steam_id, "reason": reason, "apply_timeout": apply_timeout}
        )

    def kick_player_by_name(
        self, username: str, reason: str = "Kicked by administrator", apply_timeout: bool = True
    ) -> bool:
        """Kick a player by their username (finds Steam ID automatically)"""
        from .utilities import Utilities

        utilities = Utilities(self.bridge)
        player = utilities.get_player_by_username(username)
        if not player:
            logger.warning(f"Cannot kick player: Player '{username}' not found")
            return False

        if not player.steam_id:
            logger.warning(f"Cannot kick player: No Steam ID available for '{username}'")
            return False

        return self.kick_player(player.steam_id, reason, apply_timeout)

    def send_custom_command(self, command_name: str, **kwargs) -> bool:
        """Send a custom command with arbitrary parameters"""
        return self.bridge.send_command(command_name, kwargs)
