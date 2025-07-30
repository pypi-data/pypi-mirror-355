"""
HTTP Client helper for UCode SDK
"""

import json
import requests
from typing import Dict, Any, Optional


def do_request(url: str, method: str, body: Any = None, 
               headers: Optional[Dict[str, str]] = None) -> bytes:
    """
    Standalone function to execute HTTP requests - equivalent to DoRequest() in Go.
    
    This is a utility function that can be used independently of the SDK instance.
    
    Args:
        url: The URL to make the request to
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        body: Request body data
        headers: HTTP headers to include
        
    Returns:
        bytes: Response body as bytes
        
    Raises:
        requests.RequestException: If the request fails
    """
    # Prepare request data
    json_data = None
    if body is not None:
        # Handle different body types
        if hasattr(body, '__dict__'):
            # Convert dataclass/object to dict
            json_data = body.__dict__
        elif isinstance(body, dict):
            json_data = body
        else:
            json_data = body
    
    # Prepare headers
    request_headers = {'Content-Type': 'application/json'}
    if headers:
        request_headers.update(headers)
    
    # Create HTTP client
    session = requests.Session()
    
    # Make the request
    response = session.request(
        method=method.upper(),
        url=url,
        json=json_data,
        headers=request_headers,
        timeout=30
    )
    
    # Raise an exception for bad status codes
    response.raise_for_status()
    
    return response.content