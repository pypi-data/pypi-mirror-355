"""
Lambda MCP Server - A Lambda-based MCP (Model Context Protocol) server implementation

This package provides tools for creating MCP servers that run on AWS Lambda.
"""

from .lambda_mcp import LambdaMCPServer
from .session_wrapper import SessionData
from .logging_config import setup_logging, sanitize_headers
from .requests import get, post, put, patch, delete
from . import requests

__version__ = "1.0.0"
__all__ = [
    "LambdaMCPServer", 
    "SessionData",
    "setup_logging",
    "sanitize_headers",
    "requests",
    "get",
    "post", 
    "put",
    "patch",
    "delete"
]