import socket
import threading
import signal
import select
import logging
import json
from .game_state import GameStateManager
from .event_system import EventSystem
from .message_parser import MessageParser

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Default values
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9000

# Global shutdown flag
shutdown_flag = False

# Global instances
game_state_manager = None
event_system = None
message_parser = None
current_connection = None
connection_lock = threading.Lock()


def signal_handler(sig, frame):
    global shutdown_flag
    logger.info("Received shutdown signal, shutting down gracefully...")
    shutdown_flag = True


def handle_client(conn, addr):
    global current_connection
    logger.info(f"Connected by {addr}")

    with connection_lock:
        current_connection = conn

    with conn:
        while not shutdown_flag:
            try:
                ready = select.select([conn], [], [], 1.0)
                if ready[0]:
                    data = conn.recv(4096)  # Increased buffer size for larger messages
                    if not data:
                        logger.info(f"{addr} disconnected")
                        break

                    raw_message = data.decode("utf-8").strip()
                    logger.debug(f"[{addr}] Received: {raw_message}")

                    # Parse and handle the message
                    if message_parser:
                        message_parser.handle_message(raw_message)

            except ConnectionResetError:
                logger.info(f"{addr} connection reset")
                break
            except Exception as e:
                logger.error(f"Error handling client {addr}: {e}")
                break

    with connection_lock:
        if current_connection == conn:
            current_connection = None


def send_command(command_name: str, payload: dict = None) -> bool:
    """Send a command to the connected client"""
    global current_connection

    with connection_lock:
        if not current_connection:
            logger.warning("No active connection, cannot send command")
            return False

        try:
            message = {"role": "client", "type": "command", "payload": {"command": command_name, **(payload or {})}}

            message_json = json.dumps(message) + "\n"
            current_connection.send(message_json.encode("utf-8"))
            logger.info(f"Sent command: {command_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to send command {command_name}: {e}")
            current_connection = None
            return False


def is_connected() -> bool:
    """Check if there's an active connection"""
    with connection_lock:
        return current_connection is not None


def get_game_state() -> GameStateManager:
    """Get the current game state manager instance"""
    global game_state_manager
    return game_state_manager


def get_event_system() -> EventSystem:
    """Get the current event system instance"""
    global event_system
    return event_system


def register_message_handler(message_type: str, handler):
    """Register a handler for a specific message type"""
    if event_system:
        event_system.register_handler(message_type, handler)
    else:
        logger.warning("Event system not initialized, cannot register handler")


def register_global_handler(handler):
    """Register a handler that receives all messages"""
    if event_system:
        event_system.register_global_handler(handler)
    else:
        logger.warning("Event system not initialized, cannot register global handler")


def start_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    global shutdown_flag, game_state_manager, event_system, message_parser

    # Initialize the game state and event systems
    game_state_manager = GameStateManager()
    event_system = EventSystem()
    message_parser = MessageParser(game_state_manager, event_system)

    # Only set up signal handler if we're in the main thread
    try:
        signal.signal(signal.SIGINT, signal_handler)
        logger.info("Signal handler registered")
    except ValueError as e:
        logger.warning(f"Could not register signal handler: {e}")
        logger.info("Signal handling disabled - use external shutdown mechanism")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen()
        logger.info(f"Listening on {host}:{port}")
        logger.info("Press Ctrl+C to shutdown")
        logger.info("Game state tracking initialized")

        while not shutdown_flag:
            try:
                # Use select to make accept non-blocking
                ready = select.select([server_socket], [], [], 1.0)
                if ready[0]:
                    conn, addr = server_socket.accept()
                    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
            except Exception as e:
                if not shutdown_flag:
                    logger.error(f"Server error: {e}")
                break

        logger.info("Server shutdown complete")


def shutdown_server():
    """Manually trigger server shutdown"""
    global shutdown_flag
    shutdown_flag = True
    logger.info("Server shutdown triggered")


if __name__ == "__main__":
    start_server()
