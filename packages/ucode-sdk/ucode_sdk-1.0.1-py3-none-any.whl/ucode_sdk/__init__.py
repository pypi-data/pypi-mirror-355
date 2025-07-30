"""
UCode Python SDK

A Python SDK that provides a simple and efficient way to interact with the UCode API.
This SDK offers various methods to perform CRUD operations, manage relationships,
and handle data retrieval from the UCode platform.

Usage:
    from ucode_sdk import new, Config
    
    config = Config(
        app_id="your_app_id",
        base_url="https://api.client.u-code.io"
    )
    
    sdk = new(config)
    
    # Get items
    items, response, error = sdk.items("table_name").get_list().exec()
    
    # Create item
    created, response, error = sdk.items("table_name").create(data).exec()
"""

__version__ = "1.0.0"
__author__ = "UCode Team"
__email__ = "support@u-code.io"
__license__ = "MIT"
__description__ = "UCode Python SDK - A simple and efficient way to interact with the UCode API"

# Import main classes and functions for easy access
from .sdk import UCodeSDK, new
from helper import do_request
from .config import Config
from .models import (
    Request,
    Response, 
    AuthRequest,
    RegisterResponse,
    LoginResponse,
    CreateFileResponse,
    FunctionResponse,
    User,
    Token,
    ActionBody
)

# Import exceptions
class UCodeError(Exception):
    """Base exception for UCode SDK."""
    pass

class UCodeAPIError(UCodeError):
    """Exception for API errors."""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class UCodeValidationError(UCodeError):
    """Exception for validation errors."""
    pass

# Main exports - these are what users will import
__all__ = [
    # Main SDK
    'UCodeSDK',
    'new',
    'Config',
    'do_request',
    
    # Types
    'Request',
    'Response',
    'AuthRequest',
    'RegisterResponse',
    'LoginResponse',
    'CreateFileResponse',
    'FunctionResponse',
    'User',
    'Token',
    'ActionBody',
    
    # Exceptions
    'UCodeError',
    'UCodeAPIError',
    'UCodeValidationError',
    
    # Version info
    '__version__',
    '__author__',
    '__email__',
    '__license__',
    '__description__'
]

# Convenience function for quick setup
def create_sdk(app_id: str, base_url: str = "https://api.client.u-code.io", **kwargs) -> UCodeSDK:
    """
    Quick SDK creation function.
    
    Args:
        app_id: Application ID
        base_url: API base URL
        **kwargs: Additional config parameters
        
    Returns:
        UCodeSDK: Configured SDK instance
        
    Example:
        >>> sdk = create_sdk("your_app_id")
        >>> items = sdk.items("table").get_list().exec()
    """
    config = Config(
        app_id=app_id,
        base_url=base_url,
        **kwargs
    )
    return new(config)

# Add create_sdk to exports
__all__.append('create_sdk')