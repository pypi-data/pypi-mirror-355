# Puck Bridge Python

A Python library for connecting to and interacting with [Puck](https://store.steampowered.com/app/2994020/Puck/) servers. This package provides real-time game state tracking, event handling, and server management capabilities. The [PuckBridgeMod](https://github.com/sn0w12/PuckBridgeMod) is required to be on the server.

## Features

-   Real-time game state monitoring
-   Player statistics and performance tracking
-   Event-driven architecture with custom handlers
-   Goal scoring and player action notifications
-   Team balance and player management
-   Server administration commands
-   Performance metrics and FPS monitoring
-   Easy-to-use utility functions

## Installation

```bash
pip install puck-bridge-py
```

Or install from source:

```bash
git clone https://github.com/sn0w12/puckbridgepy.git
cd puckbridge
pip install -e .
```

## Quick Start

```python
from puck_bridge_py import start_server, register_goal_handler, get_current_score

def on_goal_scored(data):
    team = data.get("team", "unknown")
    player = data.get("players", {}).get("goal", {})
    player_name = player.get("username", "unknown")

    print(f"GOAL! {player_name} scored for {team}!")
    print(f"Current score: {get_current_score()}")

# Register the goal handler
register_goal_handler(on_goal_scored)

# Start the server
start_server()
```

## Core Concepts

### Game State Management

The library automatically tracks:

-   **Players**: Names, teams, statistics, connection status
-   **Game State**: Score, time, period, game phase
-   **Performance**: FPS, server performance metrics

### Event System

Register handlers for specific game events:

-   `goal_scored` - When a goal is scored
-   `player_spawned` - When a player joins
-   `player_despawned` - When a player leaves
-   `game_state` - When game state changes

**Game Phases:**

-   `None` - No active game
-   `Warmup` - Pre-game warmup period
-   `FaceOff` - Face-off is about to begin
-   `Playing` - Active gameplay
-   `BlueScore` - Blue team scored (celebration phase)
-   `RedScore` - Red team scored (celebration phase)
-   `Replay` - Goal replay is being shown
-   `PeriodOver` - Current period has ended
-   `GameOver` - Game has completely finished

## API Reference

### Core Functions

#### Server Management

```python
start_server(host="127.0.0.1", port=9000)  # Start the Puck Bridge server with custom host/port
is_connected() -> bool  # Check if connected to game
```

#### Game State

```python
get_game_state() -> GameStateManager  # Get game state manager
get_current_score() -> Dict[str, int]  # Get current score
get_game_phase() -> str  # Get game phase (None, Warmup, FaceOff, Playing, etc.)
get_game_time() -> float  # Get current game time
is_game_in_progress() -> bool  # Check if game is actively being played
is_game_paused() -> bool  # Check if game is paused (warmup, period over)
is_game_active() -> bool  # Check if game is active (not None or GameOver)
is_period_over() -> bool  # Check if current period is over
is_game_over() -> bool  # Check if game is completely finished
is_warmup() -> bool  # Check if game is in warmup phase
is_scoring_phase() -> bool  # Check if in scoring celebration phase
```

#### Player Management

```python
get_all_players() -> Dict[int, Player]  # Get all players
get_player_by_username(username: str) -> Player  # Find player by name
get_blue_players() -> List[Player]  # Get blue team players
get_red_players() -> List[Player]  # Get red team players
get_top_scorers(limit=5) -> List[Player]  # Get top scoring players
```

#### Team Information

```python
get_team_balance() -> Dict[str, int]  # Get player count per team
get_player_count() -> int  # Get total player count
```

#### Utilities

```python
format_game_time(seconds: float) -> str  # Format time as MM:SS
format_score_string() -> str  # Get formatted score string
get_performance_stats() -> Dict[str, float]  # Get FPS and performance
```

#### Event Registration

```python
register_goal_handler(handler)  # Register goal event handler
register_player_join_handler(handler)  # Register player join handler
register_player_leave_handler(handler)  # Register player leave handler
register_game_state_handler(handler)  # Register game state handler
```

#### Commands

```python
send_system_message(message: str) -> bool  # Send message to all players
restart_game(reason: str) -> bool  # Restart the game
kick_player(steam_id: str, reason: str) -> bool  # Kick player by Steam ID
kick_player_by_name(username: str, reason: str) -> bool  # Kick by username
```

### Data Classes

#### Player

```python
@dataclass
class Player:
    client_id: int
    username: str
    state: str = "unknown"
    team: str = "none"  # "blue", "red", or "none"
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
```

#### GameState

```python
@dataclass
class GameState:
    phase: str = "unknown"  # "None", "Warmup", "FaceOff", "Playing", "BlueScore", "RedScore", "Replay", "PeriodOver", "GameOver"
    time: float = 0.0
    period: int = 0
    blue_score: int = 0
    red_score: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
```

#### Performance

```python
@dataclass
class Performance:
    current_fps: float = 0.0
    min_fps: float = 0.0
    average_fps: float = 0.0
    max_fps: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
```

## Configuration

### Server Configuration

The server can be configured with custom host and port settings:

```python
from puck_bridge_py import start_server

# Default configuration (127.0.0.1:9000)
start_server()

# Custom port
start_server(port=9001)

# Custom host and port
start_server(host="0.0.0.0", port=8080)

# Listen on all interfaces
start_server(host="0.0.0.0")
```

**Default Settings:**

-   Host: `127.0.0.1` (localhost only)
-   Port: `9000`

**Security Note:** Using `0.0.0.0` as the host will make the server accessible from other machines on the network. Only use this if you understand the security implications.

### Game Setup

1. Start your Puck Bridge Python server (with desired host/port)
2. Configure your Puck game to connect to the correct address
3. Join a game - the library will automatically start receiving data

**Default Connection:** `127.0.0.1:9000`

## Usage Examples

### Basic Game Monitoring

```python
import time
import threading
from puck_bridge_py import (
    start_server,
    get_current_score,
    get_game_phase,
    get_player_count,
    format_game_time,
    get_game_time,
)

def monitor_game():
    while True:
        if get_player_count() > 0:
            phase = get_game_phase()
            score = get_current_score()
            time_str = format_game_time(get_game_time())

            print(f"Phase: {phase} | Time: {time_str} | Score: Blue {score['blue']} - Red {score['red']}")

        time.sleep(10)

# Start monitoring in background
threading.Thread(target=monitor_game, daemon=True).start()
start_server()
```

### Advanced Event Handling

```python
from puck_bridge_py import *

def on_goal_scored(data):
    team = data.get("team")
    players = data.get("players", {})
    scorer = players.get("goal", {}).get("username", "Unknown")

    # Get assists
    assists = []
    for assist_key in ["assist1", "assist2"]:
        if assist_key in players:
            assists.append(players[assist_key].get("username", "Unknown"))

    print(f"GOAL by {scorer} ({team})")
    if assists:
        print(f"   Assists: {', '.join(assists)}")

    # Show updated standings
    top_scorers = get_top_scorers(3)
    print("   Top Scorers:")
    for i, player in enumerate(top_scorers):
        if player.goals > 0:
            print(f"     {i+1}. {player.username}: {player.goals}G {player.assists}A")

def on_player_joined(data):
    player = data.get("player", {})
    username = player.get("username", "Unknown")
    team = player.get("team", "none")

    print(f"{username} joined (Team: {team})")

    # Show team balance
    balance = get_team_balance()
    print(f"   Teams: Blue {balance['blue']} - Red {balance['red']}")

# Register handlers
register_goal_handler(on_goal_scored)
register_player_join_handler(on_player_joined)

start_server()
```

### Server Administration

```python
from puck_bridge_py import *

def admin_commands():
    while True:
        command = input("Admin> ").strip().lower()

        if command.startswith("kick "):
            username = command[5:]
            if kick_player_by_name(username, "Kicked by admin"):
                print(f"Kicked {username}")
            else:
                print(f"Failed to kick {username}")

        elif command == "restart":
            if restart_game("Game restarted by admin"):
                print("Game restarted")
            else:
                print("Failed to restart game")

        elif command.startswith("msg "):
            message = command[4:]
            if send_system_message(f"[ADMIN] {message}"):
                print("Message sent")
            else:
                print("Failed to send message")

        elif command == "players":
            players = get_all_players()
            for player in players.values():
                print(f"  {player.username} (Team: {player.team}, Goals: {player.goals})")

        elif command == "quit":
            break

# Run admin interface in background
threading.Thread(target=admin_commands, daemon=True).start()
start_server()
```

### Performance Monitoring

```python
from puck_bridge_py import *
import time

def performance_monitor():
    while True:
        if is_connected():
            stats = get_performance_stats()
            player_count = get_player_count()

            print(f"Performance: {stats['current_fps']:.1f} FPS "
                  f"(avg: {stats['average_fps']:.1f}) | "
                  f"Players: {player_count}")

        time.sleep(5)

threading.Thread(target=performance_monitor, daemon=True).start()
start_server()
```

## Event Data Structures

### Goal Scored Event

```python
{
    "team": "blue",  # or "red"
    "scores": {"blue": 1, "red": 0},
    "players": {
        "goal": {"username": "PlayerName", "clientId": 123},
        "assist1": {"username": "AssistPlayer", "clientId": 124},  # optional
        "assist2": {"username": "AssistPlayer2", "clientId": 125}  # optional
    }
}
```

### Player Spawned Event

```python
{
    "player": {
        "clientId": 123,
        "username": "PlayerName",
        "team": "blue",
        "state": "playing",
        "goals": 0,
        "assists": 0,
        # ... other player fields
    }
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
