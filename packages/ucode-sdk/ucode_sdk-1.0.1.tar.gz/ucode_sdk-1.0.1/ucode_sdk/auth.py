"""
UCode Python SDK - Authentication Module

This module provides authentication functionality,
equivalent to auth.go in the original Go SDK.
"""

import json
from typing import Dict, Any, Tuple, Protocol
from .models import (
    AuthRequest, Register, ResetPassword, Login, SendCode,
    RegisterResponse, LoginResponse, LoginWithOptionResponse, 
    SendCodeResponse, Response
)
from .config import Config
from .helper import do_request

class AuthI(Protocol):
    """
    AuthI interface - equivalent to AuthI interface in Go.
    """
    
    def register(self, data: Dict[str, Any]) -> 'Register':
        """
        Register is a function that registers a new user with the provided data.

        Works for [Mongo, Postgres]

        sdk.auth().register(data).exec()

        Use this method to create new users with basic or custom fields for authentication.
        """
        ...
    
    def reset_password(self, data: Dict[str, Any]) -> 'ResetPassword':
        """
        ResetPassword is a function that resets a user's password with the provided data.

        Works for [Mongo, Postgres]

        sdk.auth().reset_password(data).exec()

        This method initiates a password reset process, often requiring additional validation
        such as email or phone verification before allowing the reset.
        """
        ...
    
    def login(self, body: Dict[str, Any]) -> 'Login':
        """Login function for user authentication."""
        ...
    
    def send_code(self, data: Dict[str, Any]) -> 'SendCode':
        """SendCode function for sending verification codes."""
        ...


class APIAuth:
    """
    APIAuth class - equivalent to APIAuth struct in Go.
    """
    
    def __init__(self, sdk_instance):
        """
        Initialize APIAuth with SDK instance.
        
        Args:
            sdk_instance: The main SDK instance
        """
        self.config = sdk_instance.config()
        self._sdk = sdk_instance
    
    def register(self, data: Dict[str, Any]) -> 'RegisterBuilder':
        """
        Register is a function that registers a new user with the provided data.

        Works for [Mongo, Postgres]

        sdk.auth().register(data).exec()

        Use this method to create new users with basic or custom fields for authentication.
        
        Args:
            data: User registration data
            
        Returns:
            RegisterBuilder: Builder for register operation
        """
        return RegisterBuilder(
            config=self.config,
            data=AuthRequest(body=data, headers={})
        )
    
    def reset_password(self, data: Dict[str, Any]) -> 'ResetPasswordBuilder':
        """
        ResetPassword is a function that resets a user's password with the provided data.

        Works for [Mongo, Postgres]

        sdk.auth().reset_password(data).exec()

        This method initiates a password reset process, often requiring additional validation
        such as email or phone verification before allowing the reset.
        
        Args:
            data: Password reset data
            
        Returns:
            ResetPasswordBuilder: Builder for reset password operation
        """
        return ResetPasswordBuilder(
            config=self.config,
            data=AuthRequest(body=data, headers={})
        )
    
    def login(self, body: Dict[str, Any]) -> 'LoginBuilder':
        """
        Login function for user authentication.
        
        Args:
            body: Login credentials
            
        Returns:
            LoginBuilder: Builder for login operation
        """
        return LoginBuilder(
            config=self.config,
            data=AuthRequest(body=body, headers={})
        )
    
    def send_code(self, data: Dict[str, Any]) -> 'SendCodeBuilder':
        """
        SendCode function for sending verification codes.
        
        Args:
            data: Send code data
            
        Returns:
            SendCodeBuilder: Builder for send code operation
        """
        return SendCodeBuilder(
            config=self.config,
            data=AuthRequest(body=data, headers={})
        )


class RegisterBuilder:
    """
    RegisterBuilder class - equivalent to Register struct operations in Go.
    """
    
    def __init__(self, config: Config, data: AuthRequest):
        """
        Initialize RegisterBuilder.
        
        Args:
            config: SDK configuration
            data: Auth request data
        """
        self.config = config
        self.data = data
    
    def headers(self, headers: Dict[str, str]) -> 'RegisterBuilder':
        """
        Set headers for the register request.
        
        Args:
            headers: HTTP headers
            
        Returns:
            RegisterBuilder: Self for chaining
        """
        self.data.headers = headers
        return self
    
    def exec(self) -> Tuple[RegisterResponse, Response, Exception]:
        """
        Execute the register request.
        
        Returns:
            Tuple of (RegisterResponse, Response, Exception)
        """
        
        
        response = Response(
            status="done",
            error="",
            data={}
        )
        
        url = f"{self.config.base_auth_url}/v2/register?project-id={self.config.project_id}"
        
        try:
            register_response_bytes = do_request(
                url=url,
                method="POST",
                body=self.data.body,
                headers=self.data.headers
            )
            
            register_object_dict = json.loads(register_response_bytes.decode('utf-8'))
            register_object = RegisterResponse(**register_object_dict)
            
            return register_object, response, None
            
        except Exception as err:
            response.data = {
                "description": str(register_response_bytes) if 'register_response_bytes' in locals() else "",
                "message": "Can't send request",
                "error": str(err)
            }
            response.status = "error"
            return RegisterResponse(), response, err


class ResetPasswordBuilder:
    """
    ResetPasswordBuilder class - equivalent to ResetPassword struct operations in Go.
    """
    
    def __init__(self, config: Config, data: AuthRequest):
        """
        Initialize ResetPasswordBuilder.
        
        Args:
            config: SDK configuration
            data: Auth request data
        """
        self.config = config
        self.data = data
    
    def headers(self, headers: Dict[str, str]) -> 'ResetPasswordBuilder':
        """
        Set headers for the reset password request.
        
        Args:
            headers: HTTP headers
            
        Returns:
            ResetPasswordBuilder: Self for chaining
        """
        self.data.headers = headers
        return self
    
    def exec(self) -> Tuple[Response, Exception]:
        """
        Execute the reset password request.
        
        Returns:
            Tuple of (Response, Exception)
        """
        response = Response(status="done", error="", data={})
        url = f"{self.config.base_auth_url}/v2/reset-password"
        
        app_id = self.config.app_id
        headers = {
            "authorization": "API-KEY",
            "X-API-KEY": app_id,
        }
        
        try:
            do_request(
                url=url,
                method="PUT",
                body=self.data.body,
                headers=headers
            )
            
            return response, None
            
        except Exception as err:
            response.data = {
                "message": "Error while reset password",
                "error": str(err)
            }
            response.status = "error"
            return response, err


class LoginBuilder:
    """
    LoginBuilder class - equivalent to Login struct operations in Go.
    """
    
    def __init__(self, config: Config, data: AuthRequest):
        """
        Initialize LoginBuilder.
        
        Args:
            config: SDK configuration
            data: Auth request data
        """
        self.config = config
        self.data = data
    
    def headers(self, headers: Dict[str, str]) -> 'LoginBuilder':
        """
        Set headers for the login request.
        
        Args:
            headers: HTTP headers
            
        Returns:
            LoginBuilder: Self for chaining
        """
        self.data.headers = headers
        return self
    
    def exec(self) -> Tuple[LoginResponse, Response, Exception]:
        """
        Execute the login request.
        
        Returns:
            Tuple of (LoginResponse, Response, Exception)
        """
        
        
        response = Response(status="done", error="", data={})
        url = f"{self.config.base_auth_url}/v2/login"
        
        if self.data.body.get("project_id") is None:
            self.data.body["project_id"] = self.config.project_id
        
        try:
            login_response_bytes = do_request(
                url=url,
                method="POST",
                body=self.data.body,
                headers=self.data.headers
            )
            
            login_object_dict = json.loads(login_response_bytes.decode('utf-8'))
            login_object = LoginResponse(**login_object_dict)
            
            return login_object, response, None
            
        except Exception as err:
            response.data = {
                "description": str(login_response_bytes) if 'login_response_bytes' in locals() else "",
                "message": "Can't send request",
                "error": str(err)
            }
            response.status = "error"
            return LoginResponse(), response, err
    
    def exec_with_option(self) -> Tuple[LoginWithOptionResponse, Response, Exception]:
        """
        Execute the login request with options.
        
        Returns:
            Tuple of (LoginWithOptionResponse, Response, Exception)
        """
        
        
        response = Response(status="done", error="", data={})
        url = f"{self.config.base_auth_url}/v2/login/with-option?project-id={self.config.project_id}"
        
        try:
            login_response_bytes = do_request(
                url=url,
                method="POST",
                body=self.data.body,
                headers=self.data.headers
            )
            
            login_object_dict = json.loads(login_response_bytes.decode('utf-8'))
            login_object = LoginWithOptionResponse(**login_object_dict)
            
            return login_object, response, None
            
        except Exception as err:
            response.data = {
                "description": str(login_response_bytes) if 'login_response_bytes' in locals() else "",
                "message": "Can't send request",
                "error": str(err)
            }
            response.status = "error"
            return LoginWithOptionResponse(), response, err


class SendCodeBuilder:
    """
    SendCodeBuilder class - equivalent to SendCode struct operations in Go.
    """
    
    def __init__(self, config: Config, data: AuthRequest):
        """
        Initialize SendCodeBuilder.
        
        Args:
            config: SDK configuration
            data: Auth request data
        """
        self.config = config
        self.data = data
    
    def headers(self, headers: Dict[str, str]) -> 'SendCodeBuilder':
        """
        Set headers for the send code request.
        
        Args:
            headers: HTTP headers
            
        Returns:
            SendCodeBuilder: Self for chaining
        """
        self.data.headers = headers
        return self
    
    def exec(self) -> Tuple[SendCodeResponse, Response, Exception]:
        """
        Execute the send code request.
        
        Returns:
            Tuple of (SendCodeResponse, Response, Exception)
        """
        
        
        response = Response(status="done", error="", data={})
        url = f"{self.config.base_auth_url}/v2/send-code"
        
        try:
            code_response_bytes = do_request(
                url=url,
                method="POST",
                body=self.data.body,
                headers=self.data.headers
            )
            
            code_object_dict = json.loads(code_response_bytes.decode('utf-8'))
            code_object = SendCodeResponse(**code_object_dict)
            
            return code_object, response, None
            
        except Exception as err:
            response.data = {
                "description": str(code_response_bytes) if 'code_response_bytes' in locals() else "",
                "message": "Can't send request",
                "error": str(err)
            }
            response.status = "error"
            return SendCodeResponse(), response, err


# Aliases for compatibility
Auth = APIAuth
AuthInterface = AuthI


__all__ = [
    'AuthI',
    'APIAuth',
    'Auth',
    'AuthInterface',
    'RegisterBuilder',
    'ResetPasswordBuilder', 
    'LoginBuilder',
    'SendCodeBuilder'
]