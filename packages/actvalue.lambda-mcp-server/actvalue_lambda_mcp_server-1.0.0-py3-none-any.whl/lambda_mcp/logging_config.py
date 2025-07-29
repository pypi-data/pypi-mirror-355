import os
import logging
from typing import Dict, List

def setup_logging():
    """Setup logging that works in both local and Lambda environments"""
    if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        # Running in AWS Lambda
        logger = logging.getLogger()
        if os.getenv("MCP_DEBUG", "false").lower() == "true":
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
    else:
        # Local development - use basicConfig
        level = logging.DEBUG if os.getenv("MCP_DEBUG", "false").lower() == "true" else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

def sanitize_headers(headers: Dict[str, str], headers_to_mask: List[str]|None = None) -> Dict[str, str]:
    """Sanitize headers by masking sensitive values for logging purposes.
    
    Args:
        headers: Dictionary of headers to sanitize
        headers_to_mask: List of header names to mask (case-insensitive)
                        Defaults to ['Authorization', 'x-api-key']
    
    Returns:
        Dictionary with sensitive header values masked
    """
    if headers_to_mask is None:
        headers_to_mask = ['authorization', 'x-api-key']
    else:
        headers_to_mask = [header.lower() for header in headers_to_mask]
    
    safe_headers = {}
    for key, value in headers.items():
        if key.lower() in headers_to_mask:
            # Special handling for Authorization header with Bearer token
            if key.lower() == 'authorization' and value.startswith('Bearer '):
                token = value[7:]  # Remove 'Bearer ' prefix
                if len(token) > 6:
                    safe_headers[key] = f"Bearer {token[:3]}***{token[-3:]}"
                else:
                    safe_headers[key] = "Bearer ***"
            else:
                # For other sensitive headers, mask the value
                if len(value) > 6:
                    safe_headers[key] = f"{value[:3]}***{value[-3:]}"
                else:
                    safe_headers[key] = "***"
        else:
            safe_headers[key] = value
    
    return safe_headers
