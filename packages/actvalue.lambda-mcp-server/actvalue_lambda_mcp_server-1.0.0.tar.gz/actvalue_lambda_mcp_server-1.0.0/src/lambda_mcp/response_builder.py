from typing import Optional, Any, Dict, List
from lambda_mcp.types import JSONRPCError, JSONRPCResponse


class ResponseBuilder:
    """Handles creation of standardized JSON-RPC responses for MCP protocol"""
    
    # def __init__(self, mcp_version: str = "0.6"):
    #     self.mcp_version = mcp_version
    
    def create_error_response(
        self, 
        code: int, 
        message: str, 
        request_id: Optional[str] = None, 
        error_content: Optional[List[Dict]] = None, 
        session_id: Optional[str] = None, 
        status_code: Optional[int] = None
    ) -> Dict:
        """Create a standardized error response"""
        error = JSONRPCError(code=code, message=message)
        response = JSONRPCResponse(jsonrpc="2.0", id=request_id, error=error, errorContent=error_content)
        
        headers = {
            "Content-Type": "application/json",
            # "MCP-Version": self.mcp_version
        }
        if session_id:
            headers["MCP-Session-Id"] = session_id
            
        return {
            "statusCode": status_code or self._error_code_to_http_status(code),
            "body": response.model_dump_json(),
            "headers": headers
        }
    
    def create_success_response(
        self, 
        result: Any, 
        request_id: Optional[str] = None, 
        session_id: Optional[str] = None
    ) -> Dict:
        """Create a standardized success response"""
        response = JSONRPCResponse(jsonrpc="2.0", id=request_id, result=result)
        
        headers = {
            "Content-Type": "application/json",
            # "MCP-Version": self.mcp_version
        }
        if session_id:
            headers["MCP-Session-Id"] = session_id
            
        return {
            "statusCode": 200,
            "body": response.model_dump_json(),
            "headers": headers
        }
    
    def create_notification_response(self) -> Dict:
        """Create a response for notifications (requests without id)"""
        return {
            "statusCode": 204,
            "body": "",
            "headers": {
                "Content-Type": "application/json", 
                # "MCP-Version": self.mcp_version
            }
        }
    
    def create_simple_response(self, status_code: int, body: str = "") -> Dict:
        """Create a simple HTTP response without JSON-RPC structure"""
        return {
            "statusCode": status_code,
            "body": body
        }
    
    def _error_code_to_http_status(self, error_code: int) -> int:
        """Map JSON-RPC error codes to HTTP status codes"""
        error_map = {
            -32700: 400,  # Parse error
            -32600: 400,  # Invalid Request
            -32601: 404,  # Method not found
            -32602: 400,  # Invalid params
            -32603: 500,  # Internal error
        }
        return error_map.get(error_code, 500)
