import logging
import urllib.request
import urllib.error
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def _request(method: str, url: str, data: Any = None, headers: Optional[Dict[str, str]] = None) -> Any:
    """Make an HTTP request and return JSON response.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: The URL to request
        data: Data to send in request body (will be JSON encoded for POST)
        headers: Optional headers dictionary
        
    Returns:
        JSON response body (can be dict, list, or other JSON types)
        
    Raises:
        ValueError: If the request fails or returns non-200 status
    """
    request_headers = headers or {}
    
    # Prepare data for POST requests
    json_data = None
    if method == 'POST' and data is not None:
        json_data = json.dumps(data).encode('utf-8')
        request_headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=json_data, headers=request_headers)
    req.get_method = lambda: method

    # log the request
    logger.debug(f"Making {method} request to {url}")
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode()
            error_msg = f"HTTP {e.code}: {error_body}"
        except:
            error_msg = f"HTTP {e.code}: Request failed"
        raise ValueError(error_msg)
    except urllib.error.URLError as e:
        raise ValueError(f"URL Error: {e.reason}")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response")


def get(url: str, headers: Optional[Dict[str, str]] = None) -> Any:
    """Make a GET request and return JSON response.
    
    Args:
        url: The URL to request
        headers: Optional headers dictionary
        
    Returns:
        JSON response body (can be dict, list, or other JSON types)
        
    Raises:
        ValueError: If the request fails or returns non-200 status
    """
    return _request('GET', url, headers=headers)


def post(url: str, data: Any = None, headers: Optional[Dict[str, str]] = None) -> Any:
    """Make a POST request with JSON data and return JSON response.
    
    Args:
        url: The URL to request
        data: Data to send in request body (will be JSON encoded)
        headers: Optional headers dictionary
        
    Returns:
        JSON response body (can be dict, list, or other JSON types)
        
    Raises:
        ValueError: If the request fails or returns non-200 status
    """
    return _request('POST', url, data=data, headers=headers)


def put(url: str, data: Any = None, headers: Optional[Dict[str, str]] = None) -> Any:
    """Make a PUT request with JSON data and return JSON response.
    
    Args:
        url: The URL to request
        data: Data to send in request body (will be JSON encoded)
        headers: Optional headers dictionary
        
    Returns:
        JSON response body (can be dict, list, or other JSON types)
        
    Raises:
        ValueError: If the request fails or returns non-200 status
    """
    return _request('PUT', url, data=data, headers=headers)


def patch(url: str, data: Any = None, headers: Optional[Dict[str, str]] = None) -> Any:
    """Make a PATCH request with JSON data and return JSON response.
    
    Args:
        url: The URL to request
        data: Data to send in request body (will be JSON encoded)
        headers: Optional headers dictionary
        
    Returns:
        JSON response body (can be dict, list, or other JSON types)
        
    Raises:
        ValueError: If the request fails or returns non-200 status
    """
    return _request('PATCH', url, data=data, headers=headers)


def delete(url: str, headers: Optional[Dict[str, str]] = None) -> Any:
    """Make a DELETE request and return JSON response.
    
    Args:
        url: The URL to request
        headers: Optional headers dictionary
        
    Returns:
        JSON response body (can be dict, list, or other JSON types)
        
    Raises:
        ValueError: If the request fails or returns non-200 status
    """
    return _request('DELETE', url, headers=headers)
