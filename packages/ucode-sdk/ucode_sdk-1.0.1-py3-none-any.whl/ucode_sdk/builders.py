"""
UCode Python SDK - Items Module (Updated)

Updated UpdateItemBuilder to use the same ApiResponse class structure.
"""

import json
from typing import Dict, List, Any, Tuple, Protocol, Optional
from urllib.parse import quote
from .models import (
    ActionBody, Request, Datas, Response, ClientApiResponse,
    ClientApiUpdateResponse, ClientApiMultipleUpdateResponse,
    GetListClientApiResponse, GetListAggregationClientApiResponse, CreateItem,
    UpdateItem, DeleteItem, GetListItem, GetSingleItem, ApiResponse
)
from .config import Config
from .helper import do_request


class UpdateItemBuilder:
    """
    UpdateItemBuilder class - equivalent to UpdateItem struct operations in Go.
    Updated to use the same ApiResponse structure as CreateItemBuilder.
    """
    
    def __init__(self, collection: str, config: Config, data: ActionBody):
        """
        Initialize UpdateItemBuilder.
        
        Args:
            collection: Collection/table name
            config: SDK configuration
            data: Action body with data and faas settings
        """
        self.collection = collection
        self.config = config
        self.data = data
    
    def disable_faas(self, is_disable: bool) -> 'UpdateItemBuilder':
        """
        Set FaaS disable flag.
        
        Args:
            is_disable: Whether to disable FaaS
            
        Returns:
            UpdateItemBuilder: Self for chaining
        """
        self.data.disable_faas = is_disable
        return self
    
    def exec_single(self) -> tuple[Optional[ApiResponse], Response, Optional[Exception]]:
        """
        Execute single update request using the same ApiResponse structure.
        
        Returns:
            Tuple of (ApiResponse, Response, Exception)
        """
        response = Response(
            status="done",
            error="",
            data={}
        )
        
        disable_faas = str(self.data.disable_faas).lower()
        url = f"{self.config.base_url}/v2/items/{self.collection}?from-ofs={disable_faas}"
        print("Update URL:", url)
        
        app_id = self.config.app_id
        headers = {
            "authorization": "API-KEY",
            "X-API-KEY": app_id,
        }
        
        request_body = {
            "data": self.data.body,
            "disable_faas": self.data.disable_faas
        }
        
        try:
            update_object_response_bytes = do_request(
                url=url,
                method="PUT",
                body=request_body,
                headers=headers
            )
            
            # Parse response using the same ApiResponse class as CreateItemBuilder
            api_response = ApiResponse.from_bytes(update_object_response_bytes)
            
            # Update response with structured data
            response.data = {
                "operation": "update_single",
                "status": api_response.status,
                "description": api_response.description,
                "custom_message": api_response.custom_message,
                "is_cached": api_response.is_cached_response(),
                "inner_data": api_response.data_container.get_all_data_fields()
            }
            
            return api_response, response, None
            
        except (ValueError, json.JSONDecodeError) as json_err:
            response.data = {
                "description": str(update_object_response_bytes.decode('utf-8')) if 'update_object_response_bytes' in locals() else "",
                "message": "Error parsing JSON response for single update",
                "error": str(json_err)
            }
            response.status = "error"
            return None, response, json_err
            
        except Exception as err:
            response.data = {
                "description": str(update_object_response_bytes.decode('utf-8')) if 'update_object_response_bytes' in locals() else "",
                "message": "Error while updating object",
                "error": str(err)
            }
            response.status = "error"
            return None, response, err
    
    def exec_multiple(self) -> tuple[Optional[ApiResponse], Response, Optional[Exception]]:
        """
        Execute multiple update request using the same ApiResponse structure.
        
        Returns:
            Tuple of (ApiResponse, Response, Exception)
        """
        response = Response(
            status="done",
            error="",
            data={}
        )
        
        disable_faas = str(self.data.disable_faas).lower()
        url = f"{self.config.base_url}/v2/items/{self.collection}?from-ofs={disable_faas}"
        print("Multiple Update URL:", url)
        
        app_id = self.config.app_id
        headers = {
            "authorization": "API-KEY",
            "X-API-KEY": app_id,
        }
        
        request_body = {
            "data": self.data.body,
            "disable_faas": self.data.disable_faas
        }
        
        try:
            multiple_update_objects_response_bytes = do_request(
                url=url,
                method="PATCH",
                body=request_body,
                headers=headers
            )
            
            # Parse response using the same ApiResponse class
            api_response = ApiResponse.from_bytes(multiple_update_objects_response_bytes)
            
            # Update response with structured data
            response.data = {
                "operation": "update_multiple",
                "status": api_response.status,
                "description": api_response.description,
                "custom_message": api_response.custom_message,
                "is_cached": api_response.is_cached_response(),
                "inner_data": api_response.data_container.get_all_data_fields()
            }
            
            return api_response, response, None
            
        except (ValueError, json.JSONDecodeError) as json_err:
            response.data = {
                "description": str(multiple_update_objects_response_bytes.decode('utf-8')) if 'multiple_update_objects_response_bytes' in locals() else "",
                "message": "Error parsing JSON response for multiple update",
                "error": str(json_err)
            }
            response.status = "error"
            return None, response, json_err
            
        except Exception as err:
            response.data = {
                "description": str(multiple_update_objects_response_bytes.decode('utf-8')) if 'multiple_update_objects_response_bytes' in locals() else "",
                "message": "Error while multiple updating objects",
                "error": str(err)
            }
            response.status = "error"
            return None, response, err

    # Convenience method for backward compatibility
    def exec(self) -> tuple[Optional[ApiResponse], Response, Optional[Exception]]:
        """
        Default exec method that calls exec_single for backward compatibility.
        
        Returns:
            Tuple of (ApiResponse, Response, Exception)
        """
        return self.exec_single()
    


class CreateItemBuilder:
    """
    CreateItemBuilder class - equivalent to CreateItem struct operations in Go.
    """
    
    def __init__(self, collection: str, config: Config, data: ActionBody):
        """
        Initialize CreateItemBuilder.
        
        Args:
            collection: Collection/table name
            config: SDK configuration
            data: Action body with data and faas settings
        """
        self.collection = collection
        self.config = config
        self.data = data
    
    def disable_faas(self, is_disable: bool) -> 'CreateItemBuilder':
        """
        Set FaaS disable flag.
        
        Args:
            is_disable: Whether to disable FaaS
            
        Returns:
            CreateItemBuilder: Self for chaining
        """
        self.data.disable_faas = is_disable
        return self
    
    def exec(self) -> tuple[Optional[ApiResponse], Response, Optional[Exception]]:
        """
        Execute create request.
        Returns:
            Tuple of (api_response, Response, Exception)
        """
        response = Response(
            status="done",
            error="",
            data={}
        )
        
        disable_faas = str(self.data.disable_faas).lower()
        url = f"{self.config.base_url}/v2/items/{self.collection}?from-ofs={disable_faas}"
        print("URL:", url)
        
        app_id = self.config.app_id
        headers = {
            "authorization": "API-KEY",
            "X-API-KEY": app_id,
        }
        
        request_body = {
            "data": self.data.body,
            "disable_faas": self.data.disable_faas
        }
        
        try:
            create_object_response_bytes = do_request(
                url=url,
                method="POST",
                body=request_body,
                headers=headers
            )
            
            # Parse response using the new ApiResponse class
            api_response = ApiResponse.from_bytes(create_object_response_bytes)
            
            # Update response with structured data
            response.data = {
                "status": api_response.status,
                "description": api_response.description,
                "custom_message": api_response.custom_message,
                "is_cached": api_response.is_cached_response(),
                "inner_data": api_response.data_container.get_all_data_fields()
            }
            
            return api_response, response, None
            
        except (ValueError, json.JSONDecodeError) as json_err:
            response.data = {
                "description": str(create_object_response_bytes.decode('utf-8')) if 'create_object_response_bytes' in locals() else "",
                "message": "Error parsing JSON response",
                "error": str(json_err)
            }
            response.status = "error"
            return None, response, json_err
            
        except Exception as err:
            response.data = {
                "description": str(create_object_response_bytes.decode('utf-8')) if 'create_object_response_bytes' in locals() else "",
                "message": "Can't send request",
                "error": str(err)
            }
            response.status = "error"
            return None, response, err

class DeleteItemBuilder:
    """
    DeleteItemBuilder class - equivalent to DeleteItem struct operations in Go.
    Updated with proper error handling and response parsing.
    """
    
    def __init__(self, collection: str, config: Config, disable_faas: bool):
        """
        Initialize DeleteItemBuilder.
        
        Args:
            collection: Collection/table name
            config: SDK configuration
            disable_faas: Whether to disable FaaS
        """
        self.collection = collection
        self.config = config
        self.disable_faas = disable_faas
        self.id = ""
    
    def disable_faas(self, disable: bool) -> 'DeleteItemBuilder':
        """
        Set FaaS disable flag.
        
        Args:
            disable: Whether to disable FaaS
            
        Returns:
            DeleteItemBuilder: Self for chaining
        """
        self.disable_faas = disable
        return self
    
    def single(self, id: str) -> 'DeleteItemBuilder':
        """
        Set single item ID for deletion.
        
        Args:
            id: Item ID to delete
            
        Returns:
            DeleteItemBuilder: Self for chaining
        """
        self.id = id
        return self
    
    def exec(self) -> Tuple[Optional[ApiResponse], Response, Optional[Exception]]:
        """
        Execute single delete request with proper response handling.
        
        Returns:
            Tuple of (ApiResponse, Response, Exception)
        """
        response = Response(status="done", error="", data={})
        
        # Validate ID
        if not self.id:
            error = Exception("ID is required for single delete operation")
            response.data = {
                "message": "Error while deleting object",
                "error": "ID is required for single delete operation"
            }
            response.status = "error"
            return None, response, error
        
        # Construct URL - fix the boolean parameter
        disable_faas_str = str(self.disable_faas).lower()
        url = f"{self.config.base_url}/v2/items/{self.collection}/{self.id}?from-ofs={disable_faas_str}"
        print(f"Delete URL: {url}")
        
        app_id = self.config.app_id
        headers = {
            "authorization": "API-KEY",
            "X-API-KEY": app_id,
        }
        
        try:
            delete_response_bytes = do_request(
                url=url,
                method="DELETE",
                body=None,  # DELETE requests typically don't have a body
                headers=headers
            )
            
            # Handle empty response (common for DELETE operations)
            if not delete_response_bytes or delete_response_bytes.strip() == b'':
                # Success with empty response
                response.data = {
                    "message": "Object deleted successfully",
                    "deleted_id": self.id,
                    "operation": "delete_single"
                }
                # Create a mock ApiResponse for consistency
                mock_response_data = {
                    "status": "SUCCESS",
                    "description": "Object deleted successfully",
                    "custom_message": None,
                    "data": {
                        "data": {"deleted_id": self.id},
                        "is_cached": False
                    }
                }
                api_response = ApiResponse(mock_response_data)
                return api_response, response, None
            
            # Try to parse JSON response if present
            try:
                response_text = delete_response_bytes.decode('utf-8')
                print(f"Delete response: {response_text}")
                
                # Handle different response formats
                if response_text.strip():
                    response_data = json.loads(response_text)
                    api_response = ApiResponse(response_data)
                    
                    response.data = {
                        "message": "Object deleted successfully",
                        "deleted_id": self.id,
                        "operation": "delete_single",
                        "status": api_response.status,
                        "description": api_response.description,
                        "is_cached": api_response.is_cached_response(),
                        "inner_data": api_response.data_container.get_all_data_fields()
                    }
                    
                    return api_response, response, None
                else:
                    # Empty response - still success
                    response.data = {
                        "message": "Object deleted successfully",
                        "deleted_id": self.id,
                        "operation": "delete_single"
                    }
                    return None, response, None
                    
            except json.JSONDecodeError:
                # Not JSON - might be plain text success message
                response_text = delete_response_bytes.decode('utf-8')
                response.data = {
                    "message": "Object deleted successfully",
                    "deleted_id": self.id,
                    "operation": "delete_single",
                    "raw_response": response_text
                }
                return None, response, None
            
        except Exception as err:
            error_message = str(err)
            print(f"Delete error: {error_message}")
            
            # Check if it's an HTTP error with specific status codes
            if "400" in error_message and "Bad Request" in error_message:
                # 400 error might still mean successful deletion in some APIs
                # Let's check what the actual issue is
                response.data = {
                    "message": "Delete request completed with warnings",
                    "deleted_id": self.id,
                    "warning": "Received 400 status but operation may have succeeded",
                    "error": error_message
                }
                response.status = "warning"
                return None, response, Exception(f"HTTP 400 - {error_message}")
            
            # Other errors
            response.data = {
                "message": "Error while deleting object",
                "error": error_message,
                "deleted_id": self.id if self.id else "unknown"
            }
            response.status = "error"
            return None, response, err


class DeleteMultipleItemBuilder:
    """
    DeleteMultipleItemBuilder class with improved error handling.
    """
    
    def __init__(self, collection: str, config: Config, disable_faas: bool, ids: list[str]):
        self.collection = collection
        self.config = config
        self.disable_faas = disable_faas
        self.ids = ids
    
    def exec(self) -> Tuple[Optional[ApiResponse], Response, Optional[Exception]]:
        """
        Execute multiple delete request with proper response handling.
        
        Returns:
            Tuple of (ApiResponse, Response, Exception)
        """
        response = Response(status="done", error="", data={})
        
        if len(self.ids) == 0:
            error = Exception("IDs list is empty")
            response.data = {
                "message": "Error while deleting objects",
                "error": "IDs list is empty"
            }
            response.status = "error"
            return None, response, error
        
        disable_faas_str = str(self.disable_faas).lower()
        url = f"{self.config.base_url}/v2/items/{self.collection}?from-ofs={disable_faas_str}"
        
        app_id = self.config.app_id
        headers = {
            "authorization": "API-KEY",
            "X-API-KEY": app_id,
        }
        
        request_body = {"ids": self.ids}
        
        try:
            delete_response_bytes = do_request(
                url=url,
                method="DELETE",
                body=request_body,
                headers=headers
            )
            
            # Handle response similar to single delete
            if not delete_response_bytes or delete_response_bytes.strip() == b'':
                response.data = {
                    "message": "Objects deleted successfully",
                    "deleted_ids": self.ids,
                    "operation": "delete_multiple",
                    "count": len(self.ids)
                }
                return None, response, None
            
            # Try to parse JSON response
            try:
                response_text = delete_response_bytes.decode('utf-8')
                response_data = json.loads(response_text)
                api_response = ApiResponse(response_data)
                
                response.data = {
                    "message": "Objects deleted successfully",
                    "deleted_ids": self.ids,
                    "operation": "delete_multiple",
                    "count": len(self.ids),
                    "status": api_response.status,
                    "description": api_response.description
                }
                
                return api_response, response, None
                
            except json.JSONDecodeError:
                response.data = {
                    "message": "Objects deleted successfully",
                    "deleted_ids": self.ids,
                    "operation": "delete_multiple",
                    "count": len(self.ids)
                }
                return None, response, None
            
        except Exception as err:
            response.data = {
                "message": "Error while deleting objects",
                "error": str(err),
                "attempted_ids": self.ids
            }
            response.status = "error"
            return None, response, err

