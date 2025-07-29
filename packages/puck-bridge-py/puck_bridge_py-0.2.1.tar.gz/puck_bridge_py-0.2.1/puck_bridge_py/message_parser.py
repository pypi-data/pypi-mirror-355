import json
import logging
from typing import Dict, Any, Optional
from .game_state import GameStateManager
from .event_system import EventSystem

logger = logging.getLogger(__name__)


class MessageParser:
    def __init__(self, game_state_manager: GameStateManager, event_system: EventSystem):
        self.game_state = game_state_manager
        self.event_system = event_system

        # Register built-in handlers
        self._register_builtin_handlers()

    def _register_builtin_handlers(self):
        """Register the built-in message handlers"""
        self.event_system.register_handler("game_state", self._handle_game_state)
        self.event_system.register_handler("performance", self._handle_performance)
        self.event_system.register_handler("player_spawned", self._handle_player_spawned)
        self.event_system.register_handler("player_despawned", self._handle_player_despawned)
        self.event_system.register_handler("player_state_changed", self._handle_player_state_changed)
        self.event_system.register_handler("player_property_changed", self._handle_player_property_changed)
        self.event_system.register_handler("goal_scored", self._handle_goal_scored)

    def parse_message(self, raw_message: str) -> Optional[Dict[str, Any]]:
        """Parse a raw message string into a structured message"""
        try:
            message = json.loads(raw_message)

            # Validate message structure
            if not isinstance(message, dict):
                logger.warning("Message is not a JSON object")
                return None

            if "role" not in message or "type" not in message or "payload" not in message:
                logger.warning("Message missing required fields (role, type, payload)")
                return None

            return message

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}, raw_message: {raw_message}")
            return None

    def handle_message(self, raw_message: str):
        """Parse and handle an incoming message (may contain multiple JSON objects)"""
        # Split by newlines to handle multiple JSON objects
        lines = raw_message.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:  # Skip empty lines
                continue

            message = self.parse_message(line)
            if not message:
                continue

            self._process_single_message(message)

    def _process_single_message(self, message: Dict[str, Any]):
        """Process a single parsed message"""
        payload = message.get("payload", {})
        message_type = message.get("type")

        # For server messages, look for category in payload
        if message.get("role") == "server":
            if message_type == "event" and "category" in payload:
                category = payload["category"]
                self.event_system.dispatch_message(category, payload)
            elif message_type == "game_state":
                self.event_system.dispatch_message("game_state", payload)
            elif message_type == "status" and payload.get("type") == "performance":
                self.event_system.dispatch_message("performance", payload)
            else:
                # Generic message type
                self.event_system.dispatch_message(message_type, payload)
        else:
            # For other roles, use the message type directly
            self.event_system.dispatch_message(message_type, payload)

    def _handle_game_state(self, data: Dict[str, Any]):
        """Handle game state updates"""
        logger.debug(f"Updating game state: {data}")
        self.game_state.update_game_state(data)

    def _handle_performance(self, data: Dict[str, Any]):
        """Handle performance data"""
        logger.debug(f"Updating performance: {data}")
        self.game_state.update_performance(data)

    def _handle_player_spawned(self, data: Dict[str, Any]):
        """Handle player spawn events"""
        if "player" in data:
            player_data = data["player"]
            client_id = player_data.get("clientId")
            if client_id is not None:
                logger.info(f"Player spawned: {player_data.get('username', 'unknown')} (ID: {client_id})")
                self.game_state.update_player(client_id, player_data)

    def _handle_player_despawned(self, data: Dict[str, Any]):
        """Handle player despawn events"""
        if "player" in data:
            player_data = data["player"]
            client_id = player_data.get("clientId")
            if client_id is not None:
                logger.info(f"Player despawned: {player_data.get('username', 'unknown')} (ID: {client_id})")
                self.game_state.remove_player(client_id)

    def _handle_player_state_changed(self, data: Dict[str, Any]):
        """Handle player state changes"""
        client_id = data.get("clientId")
        username = data.get("username", "unknown")
        old_state = data.get("oldState")
        new_state = data.get("newState")

        logger.info(f"Player {username} state changed: {old_state} -> {new_state}")

        if client_id is not None:
            # Update the player's state
            player_data = {"state": new_state}
            if "player" in data:
                player_data.update(data["player"])
            self.game_state.update_player(client_id, player_data)

    def _handle_player_property_changed(self, data: Dict[str, Any]):
        """Handle player property changes"""
        client_id = data.get("clientId")
        username = data.get("username", "unknown")
        property_name = data.get("property")
        old_value = data.get("oldValue")
        new_value = data.get("newValue")

        logger.debug(f"Player {username} {property_name} changed: {old_value} -> {new_value}")

        if client_id is not None:
            # Update the specific property
            player_data = {property_name: new_value}
            if "player" in data:
                player_data.update(data["player"])
            self.game_state.update_player(client_id, player_data)

    def _handle_goal_scored(self, data: Dict[str, Any]):
        """Handle goal scored events"""
        team = data.get("team", "unknown")
        scores = data.get("scores", {})

        goal_player = data.get("players", {}).get("goal")
        goal_player_name = goal_player.get("username", "unknown") if goal_player else "unknown"

        logger.info(
            f"GOAL! {goal_player_name} scored for {team}! Score: Blue {scores.get('blue', 0)} - Red {scores.get('red', 0)}"
        )

        # Update game state with new scores
        if scores:
            self.game_state.update_game_state({"scores": scores})

        # Store goal data for reference
        self.game_state.set_last_goal_data(data)
