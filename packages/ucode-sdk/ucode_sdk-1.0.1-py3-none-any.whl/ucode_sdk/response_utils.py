"""
Response handling utilities for UCode SDK.
"""

from typing import Dict, Any, List


class DynamicResponse:
    """
    Dynamic response object that can handle any JSON structure.
    This is more flexible than rigid dataclasses for API responses.
    """
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize with dictionary data.
        
        Args:
            data: Dictionary data from API response
        """
        self._raw_data = data
        self._setup_attributes(data)
    
    def _setup_attributes(self, data: Dict[str, Any], prefix: str = ""):
        """
        Recursively set up attributes from dictionary data.
        
        Args:
            data: Dictionary data
            prefix: Attribute prefix for nested objects
        """
        if isinstance(data, dict):
            for key, value in data.items():
                attr_name = f"{prefix}{key}" if prefix else key
                
                if isinstance(value, dict):
                    # Create nested DynamicResponse for dict values
                    setattr(self, attr_name, DynamicResponse(value))
                elif isinstance(value, list):
                    # Handle lists
                    processed_list = []
                    for item in value:
                        if isinstance(item, dict):
                            processed_list.append(DynamicResponse(item))
                        else:
                            processed_list.append(item)
                    setattr(self, attr_name, processed_list)
                else:
                    # Set primitive values directly
                    setattr(self, attr_name, value)
    
    def get(self, key: str, default: Any = None):
        """
        Get attribute value with default.
        
        Args:
            key: Attribute key
            default: Default value if key not found
            
        Returns:
            Attribute value or default
        """
        return getattr(self, key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert back to dictionary.
        
        Returns:
            Dictionary representation
        """
        return self._raw_data
    
    def __repr__(self) -> str:
        """String representation."""
        return f"DynamicResponse({self._raw_data})"
    
    def __str__(self) -> str:
        """String representation."""
        return str(self._raw_data)


def create_response_from_json(json_data: Dict[str, Any]) -> DynamicResponse:
    """
    Create a DynamicResponse from JSON data.
    
    Args:
        json_data: JSON dictionary data
        
    Returns:
        DynamicResponse: Response object
    """
    return DynamicResponse(json_data)


def create_empty_response() -> DynamicResponse:
    """
    Create an empty response object.
    
    Returns:
        DynamicResponse: Empty response
    """
    return DynamicResponse({})


def safe_get_nested(obj: Any, path: str, default: Any = None) -> Any:
    """
    Safely get nested attribute using dot notation.
    
    Args:
        obj: Object to traverse
        path: Dot-separated path (e.g., "data.response.count")
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    try:
        current = obj
        for part in path.split('.'):
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current
    except (AttributeError, KeyError, TypeError):
        return default