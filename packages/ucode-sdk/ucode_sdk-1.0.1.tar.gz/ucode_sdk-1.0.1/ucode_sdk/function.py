"""
UCode Python SDK - Function Module

This module provides server-side function invocation functionality,
equivalent to function.go in the original Go SDK.
"""

import json
from typing import Dict, Any, Tuple, Protocol
from .models import Request, FunctionResponse, Response
from .config import Config


class FunctionI(Protocol):
    """
    FunctionI interface - equivalent to FunctionI interface in Go.
    Function interface defines methods for invoking functions.
    """
    
    def invoke(self, data: Dict[str, Any]) -> 'APIFunction':
        """
        Invoke a server-side function with the provided data.
        
        Args:
            data: Data to pass to the function
            
        Returns:
            APIFunction: Function builder for execution
        """
        ...


class APIFunction:
    """
    APIFunction class - equivalent to APIFunction struct in Go.
    APIFunction struct implements FunctionInterface.
    """
    
    def __init__(self, sdk_instance=None, path: str = "", config: Config = None, request: Request = None):
        """
        Initialize APIFunction.
        
        Args:
            sdk_instance: The main SDK instance (for initial creation)
            path: Function path
            config: SDK configuration (for chained creation)
            request: Request data (for chained creation)
        """
        if sdk_instance is not None:
            # Initial creation from SDK
            self.config = sdk_instance.config()
            self.path = path
            self.request = None
        else:
            # Chained creation from invoke()
            self.config = config
            self.path = path
            self.request = request
    
    def invoke(self, data: Dict[str, Any]) -> 'APIFunction':
        """
        Invoke a server-side function with the provided data.
        
        Args:
            data: Data to pass to the function
            
        Returns:
            APIFunction: New function instance with request data
        """
        return APIFunction(
            config=self.config,
            path=self.path,
            request=Request(data=data, is_cached=False)
        )
    
    def exec(self) -> Tuple[FunctionResponse, Response, Exception]:
        """
        Execute the function invocation request.
        
        Returns:
            Tuple of (FunctionResponse, Response, Exception)
        """
        from .helper import do_request
        
        response = Response(
            status="done",
            error="",
            data={}
        )
        
        url = f"{self.config.base_url}/v1/invoke_function/{self.path}"
        
        app_id = self.config.app_id
        headers = {
            "authorization": "API-KEY",
            "X-API-KEY": app_id,
        }
        
        try:
            invoke_function_response_bytes = do_request(
                url=url,
                method="POST",
                body=self.request,
                headers=headers
            )
            
            invoke_object_dict = json.loads(invoke_function_response_bytes.decode('utf-8'))
            invoke_object = FunctionResponse(**invoke_object_dict)
            
            return invoke_object, response, None
            
        except Exception as err:
            response.data = {
                "description": str(invoke_function_response_bytes) if 'invoke_function_response_bytes' in locals() else "",
                "message": "Can't send request",
                "error": str(err)
            }
            response.status = "error"
            return FunctionResponse(), response, err


# Aliases for compatibility
Function = APIFunction
FunctionInterface = FunctionI


__all__ = [
    'FunctionI',
    'APIFunction',
    'Function',
    'FunctionInterface'
]