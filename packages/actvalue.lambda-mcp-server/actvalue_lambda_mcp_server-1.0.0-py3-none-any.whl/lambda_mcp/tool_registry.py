import inspect
import functools
from typing import Dict, Callable, Any, get_type_hints, List
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Handles tool registration, schema generation, and execution"""
    
    def __init__(self):
        self.tools: Dict[str, Dict] = {}
        self.tool_implementations: Dict[str, Callable] = {}
    
    def tool(self):
        """Decorator to register a function as an MCP tool.
        
        Uses function name, docstring, and type hints to generate the MCP tool schema.
        """
        def decorator(func: Callable):
            # Get function name and convert to camelCase for tool name
            func_name = func.__name__
            tool_name = ''.join([func_name.split('_')[0]] + [word.capitalize() for word in func_name.split('_')[1:]])
            
            # Get docstring and parse into description
            doc = inspect.getdoc(func) or ""
            description = doc.split('\n\n')[0]  # First paragraph is description
            
            # Get type hints
            hints = get_type_hints(func)
            return_type = hints.pop('return', Any)
            
            # Build input schema from type hints and docstring
            properties = {}
            required = []
            
            # Parse docstring for argument descriptions and annotations
            arg_descriptions = {}
            annotations = {}
            if doc:
                lines = doc.split('\n')
                in_args = False
                for line in lines:
                    line = line.strip()
                    
                    # Check for annotations in comments or special markers
                    if line.startswith('//') or line.startswith('#'):
                        # Extract title from comment
                        comment_text = line.lstrip('/#').strip()
                        if comment_text and 'title' not in annotations:
                            annotations['title'] = comment_text
                    
                    # Check for specific annotation hints
                    line_normalized = line.lower().replace('-', '')
                    if 'nonreadonly' in line_normalized:
                        annotations['readOnlyHint'] = False
                    elif 'readonly' in line_normalized:
                        annotations['readOnlyHint'] = True
                    if 'nondestructive' in line_normalized:
                        annotations['destructiveHint'] = False
                    elif 'destructive' in line_normalized:
                        annotations['destructiveHint'] = True
                    if 'nonidempotent' in line_normalized:
                        annotations['idempotentHint'] = False
                    elif 'idempotent' in line_normalized:
                        annotations['idempotentHint'] = True
                    if 'nonopenworld' in line_normalized:
                        annotations['openWorldHint'] = False
                    elif 'openworld' in line_normalized:
                        annotations['openWorldHint'] = True
                    
                    if line.startswith('Args:'):
                        in_args = True
                        continue
                    if in_args:
                        if not line or line.startswith('Returns:'):
                            break
                        if ':' in line:
                            arg_name, arg_desc = line.split(':', 1)
                            arg_descriptions[arg_name.strip()] = arg_desc.strip()

            # Build properties from type hints
            for param_name, param_type in hints.items():
                param_schema = {"type": "string"}  # Default to string
                if param_type == int:
                    param_schema["type"] = "integer"
                elif param_type == float:
                    param_schema["type"] = "number"
                elif param_type == bool:
                    param_schema["type"] = "boolean"
                
                if param_name in arg_descriptions:
                    param_schema["description"] = arg_descriptions[param_name]
                    
                properties[param_name] = param_schema
                required.append(param_name)
            
            # Create tool schema
            tool_schema = {
                "name": tool_name,
                "description": description,
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
            
            # Add annotations if any were found
            if annotations:
                tool_schema["annotations"] = annotations
            
            # Register the tool
            self.tools[tool_name] = tool_schema
            self.tool_implementations[tool_name] = func
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    def get_tools(self) -> List[Dict]:
        """Get list of all registered tools"""
        return list(self.tools.values())
    
    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is registered"""
        return tool_name in self.tools
    
    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any], authorization: str|None = None) -> Any:
        """Execute a registered tool with the given arguments
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments to pass to the tool
            authorization: Optional authorization token
            
        Returns:
            Result of tool execution
            
        Raises:
            KeyError: If tool is not found
            Exception: If tool execution fails
        """
        if tool_name not in self.tool_implementations:
            raise KeyError(f"Tool '{tool_name}' not found")
        
        func = self.tool_implementations[tool_name]
        func_signature = inspect.signature(func)
        
        # Only add authorization if the function accepts it
        if 'authorization' in func_signature.parameters and authorization:
            tool_args["authorization"] = authorization.replace("Bearer ", "").strip()
        
        return func(**tool_args)

# Example docstring with annotations:
#
# def create_record(table: str, data: dict):
#     """Create a new record in the database
#     
#     // Create Database Record
#     A non-destructive and idempotent database operation
#     
#     Args:
#         table: The table name to insert into
#         data: The record data as a dictionary
#         
#     Returns:
#         dict: The created record with generated ID
#     """
#     pass
#
# This will generate annotations:
# {
#   "title": "Create Database Record",
#   "destructiveHint": false,
#   "idempotentHint": true
# }
