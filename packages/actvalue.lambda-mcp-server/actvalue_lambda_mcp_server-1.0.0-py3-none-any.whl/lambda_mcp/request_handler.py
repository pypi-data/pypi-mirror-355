import json
import logging
from typing import Any, Dict, Optional
from contextvars import ContextVar

from .types import (
    JSONRPCRequest,
    InitializeResult,
    ServerInfo,
    Capabilities,
    TextContent,
    ErrorContent
)
from .session import SessionManager
from .tool_registry import ToolRegistry
from .response_builder import ResponseBuilder
from .logging_config import sanitize_headers

# Define the implemented protocol version for MCP
# 2.0 seems a workaround for the 2025-03-26 version in mcp-remote and/or q cli
supported_protocol_versions = ["2025-03-26", "2.0"]

logger = logging.getLogger(__name__)

class RequestHandler:
    """Handles processing of incoming Lambda requests for MCP protocol"""
    
    def __init__(
        self,
        name: str,
        version: str,
        instructions: str,
        session_manager: SessionManager,
        tool_registry: ToolRegistry,
        current_session_context: ContextVar[Optional[str]]
    ):
        self.name = name
        self.version = version
        self.instructions = instructions
        self.session_manager = session_manager
        self.tool_registry = tool_registry
        self.response_builder = ResponseBuilder()
        self.current_session_context = current_session_context
    
    def _handle_delete_request(self, session_id: Optional[str]) -> Dict:
        """Handle DELETE requests for session deletion"""
        if not session_id:
            return self.response_builder.create_simple_response(400, "Missing session ID")
            
        if self.session_manager.delete_session(session_id):
            return self.response_builder.create_simple_response(204)
        else:
            return self.response_builder.create_simple_response(404)
    
    def _handle_initialize_request(self, request: JSONRPCRequest) -> Dict:
        """Handle initialize request"""
        logger.info("Handling initialize request")
        if request.params is not None:
            client_protocol_version = request.params.get("protocolVersion")
            if client_protocol_version and client_protocol_version not in supported_protocol_versions:
                return self.response_builder.create_error_response(
                    -32600, 
                    f"Unsupported protocol version. Supported versions: {', '.join(supported_protocol_versions)}", 
                    request.id
                )
        # Create new session
        session_id = self.session_manager.create_session()
        self.current_session_context.set(session_id)
        protocol_version = client_protocol_version or supported_protocol_versions[0]
        result = InitializeResult(
            protocolVersion=protocol_version,
            serverInfo=ServerInfo(name=self.name, version=self.version),
            capabilities=Capabilities(tools={"list": True, "call": True}),
            instructions=self.instructions
        )
        return self.response_builder.create_success_response(result.model_dump(), request.id, session_id)
    
    def _handle_tools_list_request(self, request: JSONRPCRequest, session_id: str | None) -> Dict:
        """Handle tools/list request"""
        logger.info("Handling tools/list request")
        return self.response_builder.create_success_response({"tools": self.tool_registry.get_tools()}, request.id, session_id)
    
    def _handle_tools_call_request(self, request: JSONRPCRequest, session_id: str | None, authorization: Optional[str]) -> Dict:
        """Handle tools/call request"""
        if request.params is None:
            return self.response_builder.create_error_response(-32602, "Invalid params: 'params' field is required", request.id, session_id=session_id)

        tool_name = request.params.get("name")
        if not tool_name:
            return self.response_builder.create_error_response(-32602, "Invalid params: 'name' field is required", request.id, session_id=session_id)
        if not self.tool_registry.has_tool(tool_name):
            return self.response_builder.create_error_response(-32601, f"Tool '{tool_name}' not found", request.id, session_id=session_id)
        
        tool_args = request.params.get("arguments", {})
        
        try:
            result = self.tool_registry.execute_tool(tool_name, tool_args, authorization)
            content = [TextContent(text=str(result)).model_dump()]
            return self.response_builder.create_success_response({"content": content}, request.id, session_id)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            error_content = [ErrorContent(text=str(e)).model_dump()]
            return self.response_builder.create_success_response({"content": error_content, "isError": True}, request.id, session_id)
        
    def _handle_ping_request(self, request: JSONRPCRequest) -> Dict:
        """Handle pingt request. Returns empty response."""
        logger.info("Handling ping request")
        return self.response_builder.create_success_response({}, request.id)
    
    def _validate_session(self, session_id: Optional[str], request_id: Optional[str], method: str) -> Optional[Dict]:
        """Validate session for non-initialize requests. Returns error response if invalid, None if valid."""
        if session_id:
            session_data = self.session_manager.get_session(session_id)
            if session_data is None:
                return self.response_builder.create_error_response(-32000, "Invalid or expired session", request_id, status_code=404)
        elif method != "initialize" and method != "ping":
            return self.response_builder.create_error_response(-32000, "Session required", request_id, status_code=400)
        return None
    
    def handle_request(self, event: Dict, context: Any) -> Dict:
        """Handle an incoming Lambda request"""
        request_id = None
        session_id = None
        authorization = None
        
        try:
            # Log the event with sanitized headers for debugging
            sanitized_event = event.copy()
            if "headers" in sanitized_event:
                sanitized_event["headers"] = sanitize_headers(sanitized_event["headers"])
            logger.debug(f"Received event: {sanitized_event}")
            
            # Get headers (case-insensitive)
            headers = {k.lower(): v for k, v in event.get("headers", {}).items()}
            
            # Get session ID from headers
            session_id = headers.get("mcp-session-id")
            
            # Set current session ID in context
            if session_id:
                self.current_session_context.set(session_id)
            else:
                self.current_session_context.set(None)

            # Get authorization header if present
            authorization = headers.get("authorization")
            if authorization:
                logger.debug(f"Authorization header found")

            # Protocol version (draft)
            protocol_version = headers.get("mcp-protocol-version", supported_protocol_versions[0])
            if protocol_version not in supported_protocol_versions:
                logger.debug(f"Unsupported protocol version: {protocol_version}")
                return self.response_builder.create_error_response(
                    -32600, 
                    f"Unsupported protocol version. Supported versions: {', '.join(supported_protocol_versions)}", 
                    request_id, 
                    status_code=400
                )
            
            # Check HTTP method for session deletion
            if event.get("httpMethod") == "DELETE":
                return self._handle_delete_request(session_id)
            
            # Validate content type
            if headers.get("content-type") != "application/json":
                return self.response_builder.create_error_response(-32700, "Unsupported Media Type")

            # Handle missing or empty body
            request_body = event.get("body", "")
            if not request_body or request_body.strip() == "":
                return self.response_builder.create_error_response(-32700, "Empty request body")

            try:
                body = json.loads(request_body)
                logger.debug(f"Parsed request body: {body}")
                request_id = body.get("id") if isinstance(body, dict) else None
                
                # Check if this is a notification (no id field)
                if isinstance(body, dict) and "id" not in body:
                    logger.debug("Request is a notification")
                    return self.response_builder.create_notification_response()
                    
                # Validate basic JSON-RPC structure
                if not isinstance(body, dict) or body.get("jsonrpc") != "2.0" or "method" not in body:
                    return self.response_builder.create_error_response(-32700, "Parse error", request_id)
                    
            except json.JSONDecodeError:
                return self.response_builder.create_error_response(-32700, "Parse error")
            
            # Parse and validate the request
            request = JSONRPCRequest.model_validate(body)
            logger.debug(f"Validated request: {request}")
            
            # Handle initialization request
            if request.method == "initialize":
                return self._handle_initialize_request(request)
            
            # For all other requests, validate session
            session_error = self._validate_session(session_id, request.id, request.method)
            if session_error:
                return session_error
                
            # Handle different request types
            if request.method == "tools/list":
                return self._handle_tools_list_request(request, session_id)
            elif request.method == "tools/call":
                return self._handle_tools_call_request(request, session_id, authorization)
            elif request.method == "ping":
                return self._handle_ping_request(request)
            else:
                # Handle unknown methods
                return self.response_builder.create_error_response(-32601, f"Method not found: {request.method}", request.id, session_id=session_id)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return self.response_builder.create_error_response(-32000, str(e), request_id, session_id=session_id)
        finally:
            # Clear session context
            self.current_session_context.set(None)
