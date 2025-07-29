import os
from .session import SessionManager
from .tool_registry import ToolRegistry
from .request_handler import RequestHandler
from .session_wrapper import SessionWrapper, SessionData
from .logging_config import setup_logging
import logging
from typing import Callable, Optional, Any, Dict
from contextvars import ContextVar

# Setup logging at import time
setup_logging()
logger = logging.getLogger(__name__)

# Context variable to store current session ID
current_session_id: ContextVar[Optional[str]] = ContextVar('current_session_id', default=None)

class LambdaMCPServer:
    """A class to handle MCP protocol in AWS Lambda"""
    
    def __init__(
            self, 
            name: str, 
            version: str = "1.0.0", 
            instructions: str | None = None,
            cache_prefix: str = "mcp_sessions",
            redis_url: str = "redis://localhost:6379/0",
            ):
        self.name = name
        self.version = version
        self.instructions = instructions or "This is a Lambda MCP server"
        self.session_manager = SessionManager(cache_prefix=cache_prefix, redis_url=redis_url)
        self.tool_registry = ToolRegistry()
        self.session_wrapper = SessionWrapper(self.session_manager, current_session_id)
        self.request_handler = RequestHandler(
            name=self.name,
            version=self.version,
            instructions=self.instructions,
            session_manager=self.session_manager,
            tool_registry=self.tool_registry,
            current_session_context=current_session_id
        )
    
    def tool(self):
        """Decorator to register a function as an MCP tool"""
        return self.tool_registry.tool()
    
    def handle_request(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Main entry point to handle incoming Lambda requests
        Args:
            event: The incoming event data
            context: The Lambda context object
        Returns:
            A dictionary response containing the result of the request processing"""
        return self.request_handler.handle_request(event, context)
    
    def get_session(self) -> Optional[SessionData]:
        """Get the current session data wrapper.
        Returns:
            SessionData object or None if no session exists
        """
        return self.session_wrapper.get_session()

    def set_session(self, data: Dict[str, Any]) -> bool:
        """Set the entire session data.
        Args:
            data: New session data
        Returns:
            True if successful, False if no session exists
        """
        return self.session_wrapper.set_session(data)

    def update_session(self, updater_func: Callable[[SessionData], None]) -> bool:
        """Update session data using a function.
        Args:
            updater_func: Function that takes SessionData and updates it in place
        Returns:
            True if successful, False if no session exists
        """
        return self.session_wrapper.update_session(updater_func)