import socket
import threading
import signal
import select
import logging
import json
from typing import Optional, Callable
from .game_state import GameStateManager
from .event_system import EventSystem
from .message_parser import MessageParser

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Default values
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9000


class PuckBridge:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.shutdown_flag = False

        # Initialize the game state and event systems
        self.game_state_manager = GameStateManager()
        self.event_system = EventSystem()
        self.message_parser = MessageParser(self.game_state_manager, self.event_system)

        self.current_connection: Optional[socket.socket] = None
        self.connection_lock = threading.Lock()
        self.server_socket: Optional[socket.socket] = None
        self.server_thread: Optional[threading.Thread] = None

    def send_command(self, command_name: str, payload: dict = None) -> bool:
        """Send a command to the connected client"""
        with self.connection_lock:
            if not self.current_connection:
                logger.warning("No active connection, cannot send command")
                return False

            try:
                message = {"role": "client", "type": "command", "payload": {"command": command_name, **(payload or {})}}

                message_json = json.dumps(message) + "\n"
                self.current_connection.send(message_json.encode("utf-8"))
                logger.info(f"Sent command: {command_name}")
                return True

            except Exception as e:
                logger.error(f"Failed to send command {command_name}: {e}")
                self.current_connection = None
                return False

    def is_connected(self) -> bool:
        """Check if there's an active connection"""
        with self.connection_lock:
            return self.current_connection is not None

    def get_game_state(self) -> GameStateManager:
        """Get the current game state manager instance"""
        return self.game_state_manager

    def get_event_system(self) -> EventSystem:
        """Get the current event system instance"""
        return self.event_system

    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        self.event_system.register_handler(message_type, handler)

    def register_global_handler(self, handler: Callable):
        """Register a handler that receives all messages"""
        self.event_system.register_global_handler(handler)

    def _handle_client(self, conn: socket.socket, addr):
        """Handle a client connection"""
        logger.info(f"Connected by {addr}")

        with self.connection_lock:
            self.current_connection = conn

        with conn:
            while not self.shutdown_flag:
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
                        self.message_parser.handle_message(raw_message)

                except ConnectionResetError:
                    logger.info(f"{addr} connection reset")
                    break
                except Exception as e:
                    logger.error(f"Error handling client {addr}: {e}")
                    break

        with self.connection_lock:
            if self.current_connection == conn:
                self.current_connection = None

    def _signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal, shutting down gracefully...")
        self.shutdown_flag = True

    def start_server(self, blocking: bool = True):
        """Start the server"""
        if blocking:
            self._run_server()
        else:
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()

    def _run_server(self):
        """Internal server run method"""
        # Only set up signal handler if we're in the main thread
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            logger.info("Signal handler registered")
        except ValueError as e:
            logger.warning(f"Could not register signal handler: {e}")
            logger.info("Signal handling disabled - use external shutdown mechanism")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            self.server_socket = server_socket
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            logger.info(f"Listening on {self.host}:{self.port}")
            logger.info("Press Ctrl+C to shutdown")
            logger.info("Game state tracking initialized")

            while not self.shutdown_flag:
                try:
                    # Use select to make accept non-blocking
                    ready = select.select([server_socket], [], [], 1.0)
                    if ready[0]:
                        conn, addr = server_socket.accept()
                        threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()
                except Exception as e:
                    if not self.shutdown_flag:
                        logger.error(f"Server error: {e}")
                    break

            logger.info("Server shutdown complete")

    def shutdown_server(self):
        """Manually trigger server shutdown"""
        self.shutdown_flag = True
        logger.info("Server shutdown triggered")

    def wait_for_shutdown(self):
        """Wait for the server thread to complete (if running non-blocking)"""
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join()

