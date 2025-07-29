from typing import Optional, Any, Dict, Callable, TypeVar, Generic
from contextvars import ContextVar

from lambda_mcp.session import SessionManager

T = TypeVar('T')

class SessionData(Generic[T]):
    """Helper class for type-safe session data access"""
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get(self, key: str, default: T = None) -> T:
        """Get a value from session data with type safety"""
        return self._data.get(key, default)

    def set(self, key: str, value: T) -> None:
        """Set a value in session data"""
        self._data[key] = value

    def raw(self) -> Dict[str, Any]:
        """Get the raw dictionary data"""
        return self._data

class SessionWrapper:
    """Wraps session management with convenient access methods"""
    
    def __init__(self, session_manager: SessionManager, current_session_context: ContextVar[Optional[str]]):
        self.session_manager = session_manager
        self.current_session_context = current_session_context
    
    def get_session(self) -> Optional[SessionData]:
        """Get the current session data wrapper.
        
        Returns:
            SessionData object or None if no session exists
        """
        session_id = self.current_session_context.get()
        if not session_id:
            return None
        data = self.session_manager.get_session(session_id)
        return SessionData(data) if data is not None else None

    def set_session(self, data: Dict[str, Any]) -> bool:
        """Set the entire session data.
        
        Args:
            data: New session data
            
        Returns:
            True if successful, False if no session exists
        """
        session_id = self.current_session_context.get()
        if not session_id:
            return False
        return self.session_manager.update_session(session_id, data)

    def update_session(self, updater_func: Callable[[SessionData], None]) -> bool:
        """Update session data using a function.
        
        Args:
            updater_func: Function that takes SessionData and updates it in place
            
        Returns:
            True if successful, False if no session exists
        """
        session = self.get_session()
        if not session:
            return False
            
        # Update the session data
        updater_func(session)
        
        # Save back to storage
        return self.set_session(session.raw())
