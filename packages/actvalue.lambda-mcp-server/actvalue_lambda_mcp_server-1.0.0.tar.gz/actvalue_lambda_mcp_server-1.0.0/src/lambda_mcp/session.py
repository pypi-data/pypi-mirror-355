"""Session management for MCP server using Redis"""
import uuid
import time
import json
from typing import Optional, Dict, Any
import redis
import logging

logger = logging.getLogger(__name__)

# Store session in Redis with 24 hour expiry
REDIS_TTL = 24 * 60 * 60  # 24 hours in seconds

class SessionManager:
    """Manages MCP sessions using Redis"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", cache_prefix: str = "mcp_server"):
        """Initialize the session manager
        
        Args:
            redis_url: Redis connection URL
            cache_prefix: Prefix for Redis keys
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.cache_prefix = cache_prefix
        
    def create_session(self, session_data: Optional[Dict[str, Any]] = None) -> str:
        """Create a new session
        
        Args:
            session_data: Optional initial session data
            
        Returns:
            The session ID
        """
        # Generate a secure random UUID for the session
        session_id = str(uuid.uuid4())
        
        # Create session object
        session_obj = {
            'created_at': int(time.time()),
            'data': session_data or {}
        }
        
        key = f"{self.cache_prefix}_{session_id}"
        self.redis_client.setex(key, REDIS_TTL, json.dumps(session_obj))
        logger.info(f"Created session {session_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data
        
        Args:
            session_id: The session ID to look up
            
        Returns:
            Session data or None if not found
        """
        try:
            key = f"{self.cache_prefix}_{session_id}"
            session_json = self.redis_client.get(key)
            
            if not session_json:
                return None
                
            session_obj = json.loads(str(session_json))
            return session_obj.get('data', {})
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update session data
        
        Args:
            session_id: The session ID to update
            session_data: New session data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"{self.cache_prefix}_{session_id}"
            
            # Get existing session to preserve created_at
            existing_json = self.redis_client.get(key)
            if not existing_json:
                return False
                
            existing_obj = json.loads(str(existing_json))
            existing_obj['data'] = session_data
            
            # Get remaining TTL and preserve it
            ttl = self.redis_client.ttl(key)
            # Convert ttl to int to ensure proper comparison
            if isinstance(ttl, int) or (ttl is not None and hasattr(ttl, '__await__')):
                # Handle both synchronous and asynchronous Redis clients
                ttl_value = int(ttl) if isinstance(ttl, int) else -1
            else:
                ttl_value = -1
                
            if ttl_value > 0:
                self.redis_client.setex(key, ttl_value, json.dumps(existing_obj))
            else:
                self.redis_client.set(key, json.dumps(existing_obj))
                
            return True
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"{self.cache_prefix}_{session_id}"
            result = self.redis_client.delete(key)
            if result:
                logger.info(f"Deleted session {session_id}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False