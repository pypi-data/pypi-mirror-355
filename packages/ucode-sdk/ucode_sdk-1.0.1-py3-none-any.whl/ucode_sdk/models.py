"""
UCode Python SDK - Type Definitions

This module provides all the type definitions and structures,
equivalent to the types defined in the original Go SDK.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, Union, List
from .config import Config
import json

@dataclass
class Request:
    """Request structure - equivalent to Request struct in Go."""
    data: Dict[str, Any]
    is_cached: bool


@dataclass
class Argument:
    """Argument structure - equivalent to Argument struct in Go."""
    app_id: str
    table_slug: str
    request: Request
    disable_faas: bool


@dataclass
class ArgumentWithPagination:
    """ArgumentWithPagination structure - equivalent to ArgumentWithPegination struct in Go."""
    app_id: str
    table_slug: str
    request: Request
    disable_faas: bool
    limit: int
    page: int


@dataclass
class Data:
    """Data structure - equivalent to Data struct in Go."""
    app_id: str
    method: str
    object_data: Dict[str, Any]
    object_ids: List[str]
    table_slug: str
    user_id: str


# Response structures

@dataclass
class Datas:
    """Create function response body - equivalent to Datas struct in Go."""
    
    @dataclass
    class DataInner:
        data: Dict[str, Any]
    
    data: DataInner = None


@dataclass
class ClientApiResponse:
    """ClientApiResponse - equivalent to ClientApiResponse struct in Go."""
    
    @dataclass
    class ClientApiData:
        @dataclass
        class ClientApiResp:
            response: Dict[str, Any]
        
        data: ClientApiResp = None
    
    data: ClientApiData = None


@dataclass
class Response:
    """Response structure - equivalent to Response struct in Go."""
    status: str
    error: str
    data: Dict[str, Any]


@dataclass
class GetListClientApiResponse:
    """GetListClientApiResponse - equivalent to GetListClientApiResponse struct in Go."""
    
    @dataclass
    class GetListClientApiData:
        @dataclass
        class GetListClientApiResp:
            count: int
            response: List[Dict[str, Any]]
        
        data: GetListClientApiResp
    
    data: GetListClientApiData


@dataclass
class GetListAggregationClientApiResponse:
    """GetListAggregationClientApiResponse - equivalent to GetListAggregationClientApiResponse struct in Go."""
    
    @dataclass
    class DataOuter:
        @dataclass
        class DataMiddle:
            data: List[Dict[str, Any]]
        
        data: DataMiddle
    
    data: DataOuter


@dataclass
class ClientApiUpdateResponse:
    """ClientApiUpdateResponse - equivalent to ClientApiUpdateResponse struct in Go."""
    
    @dataclass
    class DataInner:
        table_slug: str
        data: Dict[str, Any]
    
    status: str
    description: str
    data: DataInner


@dataclass
class ClientApiMultipleUpdateResponse:
    """ClientApiMultipleUpdateResponse - equivalent to ClientApiMultipleUpdateResponse struct in Go."""
    
    @dataclass
    class DataOuter:
        @dataclass
        class DataInner:
            objects: List[Dict[str, Any]]
        
        data: DataInner
    
    status: str
    description: str
    data: DataOuter


@dataclass
class ResponseError:
    """ResponseError structure - equivalent to ResponseError struct in Go."""
    status_code: int
    description: Any
    error_message: str
    client_error_message: str


@dataclass
class ActionBody:
    """ActionBody structure - equivalent to ActionBody struct in Go."""
    body: Dict[str, Any]
    disable_faas: bool


@dataclass
class AuthRequest:
    """AuthRequest structure - equivalent to AuthRequest struct in Go."""
    body: Dict[str, Any]
    headers: Dict[str, str]


@dataclass
class APIItem:
    """APIItem structure - equivalent to APIItem struct in Go."""
    collection: str
    config: 'Config'


@dataclass
class CreateItem:
    """CreateItem structure - equivalent to CreateItem struct in Go."""
    collection: str
    config: 'Config'
    data: ActionBody


@dataclass
class DeleteItem:
    """DeleteItem structure - equivalent to DeleteItem struct in Go."""
    collection: str
    config: 'Config'
    disable_faas: bool
    id: str


@dataclass
class DeleteMultipleItem:
    """DeleteMultipleItem structure - equivalent to DeleteMultipleItem struct in Go."""
    collection: str
    config: 'Config'
    disable_faas: bool
    ids: List[str]


@dataclass
class UpdateItem:
    """UpdateItem structure - equivalent to UpdateItem struct in Go."""
    collection: str
    config: 'Config'
    data: ActionBody


@dataclass
class GetSingleItem:
    """GetSingleItem structure - equivalent to GetSingleItem struct in Go."""
    collection: str
    config: 'Config'
    guid: str


@dataclass
class GetListItem:
    """GetListItem structure - equivalent to GetListItem struct in Go."""
    collection: str
    config: 'Config'
    request: Request
    limit: int
    page: int


@dataclass
class GetListAggregation:
    """GetListAggregation structure - equivalent to GetListAggregation struct in Go."""
    collection: str
    config: 'Config'
    request: Request


@dataclass
class Register:
    """Register structure - equivalent to Register struct in Go."""
    config: 'Config'
    data: AuthRequest


@dataclass
class ResetPassword:
    """ResetPassword structure - equivalent to ResetPassword struct in Go."""
    config: 'Config'
    data: AuthRequest


@dataclass
class Login:
    """Login structure - equivalent to Login struct in Go."""
    config: 'Config'
    data: AuthRequest


@dataclass
class SendCode:
    """SendCode structure - equivalent to SendCode struct in Go."""
    config: 'Config'
    data: AuthRequest


@dataclass
class APIAuth:
    """APIAuth structure - equivalent to APIAuth struct in Go."""
    config: 'Config'


@dataclass
class APIFiles:
    """APIFiles structure - equivalent to APIFiles struct in Go."""
    config: 'Config'


@dataclass
class UploadFile:
    """UploadFile structure - equivalent to UploadFile struct in Go."""
    config: 'Config'
    path: str


@dataclass
class DeleteFile:
    """DeleteFile structure - equivalent to DeleteFile struct in Go."""
    config: 'Config'
    id: str


@dataclass
class APIFunction:
    """APIFunction structure - equivalent to APIFunction struct in Go."""
    config: 'Config'
    request: Request
    path: str


@dataclass
class User:
    """User structure - equivalent to User struct in Go."""
    id: str
    login: str
    password: str
    email: str
    phone: str
    name: str
    project_id: str
    role_id: str
    client_type_id: str


@dataclass
class Token:
    """Token structure - equivalent to Token struct in Go."""
    access_token: str
    refresh_token: str
    created_at: str
    updated_at: str
    expires_at: str
    refresh_in_seconds: int


@dataclass
class RegisterResponse:
    """RegisterResponse structure - equivalent to RegisterResponse struct in Go."""
    
    @dataclass
    class DataInner:
        user_found: bool
        user_id: str
        token: Optional[Token]
        login_table_slug: str
        environment_id: str
        user: Optional[User]
        user_id_auth: str
    
    status: str
    description: str
    data: DataInner


@dataclass
class CreateFileResponse:
    """CreateFileResponse structure - equivalent to CreateFileResponse struct in Go."""
    
    @dataclass
    class DataInner:
        id: str
        title: str
        storage: str
        file_name_disk: str
        file_name_download: str
        link: str
        file_size: int
    
    status: str
    description: str
    data: DataInner
    custom_message: str


@dataclass
class FunctionResponse:
    """FunctionResponse structure - equivalent to FunctionResponse struct in Go."""
    status: str
    description: str
    data: Any
    custom_message: Any


@dataclass
class Session:
    """Session structure - equivalent to Session struct in Go."""
    id: str
    project_id: str
    client_type_id: str
    user_id: str
    role_id: str
    created_at: str
    updated_at: str
    user_id_auth: str


@dataclass
class LoginWithOptionResponse:
    """LoginWithOptionResponse structure - equivalent to LoginWithOptionResponse struct in Go."""
    
    @dataclass
    class DataInner:
        user_found: bool
        user_id: str
        token: Optional[Token]
        sessions: List[Session]
        user_data: Dict[str, Any]
    
    status: str
    description: str
    data: DataInner


@dataclass
class LoginResponse:
    """LoginResponse structure - equivalent to LoginResponse struct in Go."""
    
    @dataclass
    class DataInner:
        user_found: bool
        client_type: Dict[str, Any]
        user_id: str
        role: Dict[str, Any]
        token: Optional[Token]
        permissions: List[Dict[str, Any]]
        sessions: List[Session]
        login_table_slug: str
        app_permissions: List[Dict[str, Any]]
        resource_id: str
        environment_id: str
        user: Optional[User]
        global_permission: Dict[str, Any]
        user_data: Dict[str, Any]
        user_id_auth: str
    
    status: str
    description: str
    data: DataInner


@dataclass
class SendCodeResponse:
    """SendCodeResponse structure - equivalent to SendCodeResponse struct in Go."""
    
    @dataclass
    class DataInner:
        sms_id: str
        google_acces: bool
        user_found: bool
    
    status: str
    description: str
    data: DataInner

class DataContainer:
    """Class to handle the nested data structure"""
    
    def __init__(self, data_dict: Dict[str, Any]):
        self.data: Dict[str, Any] = data_dict.get('data', {})
        self.is_cached: bool = data_dict.get('is_cached', False)
    
    def get_data_field(self, field_name: str, default: Any = None) -> Any:
        """Get a field from the inner data dictionary"""
        return self.data.get(field_name, default)
    
    def has_data_field(self, field_name: str) -> bool:
        """Check if a field exists in the inner data dictionary"""
        return field_name in self.data
    
    def get_all_data_fields(self) -> Dict[str, Any]:
        """Get all fields from the inner data dictionary"""
        return self.data.copy()
    
    def __repr__(self):
        return f"DataContainer(data={self.data}, is_cached={self.is_cached})"

class ApiResponse:
    """Main class to capture the complete API response structure"""
    
    def __init__(self, response_dict: Dict[str, Any]):
        self.custom_message: Optional[str] = response_dict.get('custom_message')
        self.description: str = response_dict.get('description', '')
        self.status: str = response_dict.get('status', '')
        
        # Handle the nested data structure
        data_section = response_dict.get('data', {})
        self.data_container = DataContainer(data_section)
        
        # Store raw response for debugging
        self.raw_response = response_dict
    
    @classmethod
    def from_json_string(cls, json_string: str) -> 'ApiResponse':
        """Create ApiResponse from JSON string"""
        try:
            response_dict = json.loads(json_string)
            return cls(response_dict)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")
    
    @classmethod
    def from_bytes(cls, response_bytes: bytes) -> 'ApiResponse':
        """Create ApiResponse from bytes"""
        try:
            json_string = response_bytes.decode('utf-8')
            return cls.from_json_string(json_string)
        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot decode bytes to UTF-8: {e}")
    
    def get_data_field(self, field_name: str, default: Any = None) -> Any:
        """Convenience method to get a field from the inner data"""
        return self.data_container.get_data_field(field_name, default)
    
    def is_success(self) -> bool:
        """Check if the response indicates success (customize based on your API)"""
        return self.status.upper() in ['SUCCESS', 'CREATED', 'OK', 'DONE']
    
    def is_cached_response(self) -> bool:
        """Check if this is a cached response"""
        return self.data_container.is_cached
    
    def __repr__(self):
        return (f"ApiResponse(status='{self.status}', description='{self.description}', "
                f"custom_message={self.custom_message}, data_container={self.data_container})")


__all__ = [
    'Request',
    'Argument', 
    'ArgumentWithPagination',
    'Data',
    'Datas',
    'ClientApiResponse',
    'Response',
    'GetListClientApiResponse',
    'GetListAggregationClientApiResponse',
    'ClientApiUpdateResponse',
    'ClientApiMultipleUpdateResponse',
    'ResponseError',
    'ActionBody',
    'AuthRequest',
    'APIItem',
    'CreateItem',
    'DeleteItem',
    'DeleteMultipleItem',
    'UpdateItem',
    'GetSingleItem',
    'GetListItem',
    'GetListAggregation',
    'Register',
    'ResetPassword',
    'Login',
    'SendCode',
    'APIAuth',
    'APIFiles',
    'UploadFile',
    'DeleteFile',
    'APIFunction',
    'User',
    'Token',
    'RegisterResponse',
    'CreateFileResponse',
    'FunctionResponse',
    'Session',
    'LoginWithOptionResponse',
    'LoginResponse',
    'SendCodeResponse'
]