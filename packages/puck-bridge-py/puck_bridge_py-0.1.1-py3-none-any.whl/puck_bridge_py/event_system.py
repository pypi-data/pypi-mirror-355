from typing import Dict, List, Callable, Any
import logging

logger = logging.getLogger(__name__)


class EventSystem:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._global_handlers: List[Callable] = []

    def register_handler(self, message_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Register a handler for a specific message type"""
        if message_type not in self._handlers:
            self._handlers[message_type] = []
        self._handlers[message_type].append(handler)
        logger.info(f"Registered handler for message type: {message_type}")

    def register_global_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        """Register a handler that receives all messages"""
        self._global_handlers.append(handler)
        logger.info("Registered global message handler")

    def unregister_handler(self, message_type: str, handler: Callable):
        """Unregister a specific handler"""
        if message_type in self._handlers and handler in self._handlers[message_type]:
            self._handlers[message_type].remove(handler)
            logger.info(f"Unregistered handler for message type: {message_type}")

    def unregister_global_handler(self, handler: Callable):
        """Unregister a global handler"""
        if handler in self._global_handlers:
            self._global_handlers.remove(handler)
            logger.info("Unregistered global message handler")

    def dispatch_message(self, message_type: str, data: Dict[str, Any]):
        """Dispatch a message to all registered handlers"""
        # Call global handlers first
        for handler in self._global_handlers:
            try:
                handler(message_type, data)
            except Exception as e:
                logger.error(f"Error in global handler: {e}")

        # Call specific handlers
        if message_type in self._handlers:
            for handler in self._handlers[message_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in handler for {message_type}: {e}")

    def get_registered_types(self) -> List[str]:
        """Get all registered message types"""
        return list(self._handlers.keys())
