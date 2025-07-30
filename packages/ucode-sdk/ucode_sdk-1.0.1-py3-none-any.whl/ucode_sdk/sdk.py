"""
UCode Python SDK - Main SDK Module

This module provides the main SDK interface and implementation,
equivalent to sdk.go in the original Go SDK.
"""

import json
import requests
from typing import Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod

# Optional MQTT import
import paho.mqtt.client as mqtt

from .config import Config
from .items import ItemsI
from .auth import AuthI
from .files import FilesI
from .function import FunctionI
from .function import Function


class UcodeApis(Protocol):
    """
    Interface for UCode APIs - equivalent to UcodeApis interface in Go.
    This defines the contract that all UCode SDK implementations must follow.
    """
    
    def items(self, collection: str) -> ItemsI:
        """
        Items returns an interface to interact with items within a specified collection.
        Items are objects within a Collection which contain values for one or more fields.
        Each item represents a record in your database, allowing CRUD operations.
        
        Usage:
            sdk.items("collection_name").create(data).exec()
        
        This enables you to manage items in collections across databases, 
        such as MongoDB and PostgreSQL.
        
        Args:
            collection: The name of the collection to interact with
            
        Returns:
            ItemsI: Interface for items operations
        """
        ...
    
    def auth(self) -> AuthI:
        """
        Auth returns an interface for handling user authentication and authorization operations.
        Use this interface to manage user registration, login, password resets, and other
        authentication-related tasks.
        
        Usage:
            sdk.auth().register(data).exec()
        
        Supports various authentication workflows compatible with both MongoDB and PostgreSQL.
        
        Returns:
            AuthI: Interface for authentication operations
        """
        ...
    
    def files(self) -> FilesI:
        """
        Files returns an interface for file management operations.
        Use this interface to upload, delete, or manage files stored on the server, allowing
        for easy integration of file-based data alongside other operations.
        
        Usage:
            sdk.files().upload("file_path").exec()
        
        Designed for compatibility with both MongoDB and PostgreSQL for consistent file management.
        
        Returns:
            FilesI: Interface for file operations
        """
        ...
    
    def function(self, path: str) -> FunctionI:
        """
        Function returns an interface for invoking server-side functions.
        This interface enables the execution of predefined or custom server functions,
        facilitating complex data processing and automation workflows.
        
        Usage:
            sdk.function("function_path").invoke(data).exec()
        
        Supported across MongoDB and PostgreSQL, providing flexibility for backend processing.
        
        Args:
            path: The path to the server function
            
        Returns:
            FunctionI: Interface for function operations
        """
        ...
    
    def config(self) -> Config:
        """
        Get the current configuration object.
        
        Returns:
            Config: The SDK configuration
        """
        ...
    
    def do_request(self, url: str, method: str, body: Any = None, 
                   headers: Optional[Dict[str, str]] = None) -> bytes:
        """
        Execute an HTTP request with the given parameters.
        
        Args:
            url: The URL to make the request to
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            body: Request body data
            headers: HTTP headers to include
            
        Returns:
            bytes: Response body as bytes
            
        Raises:
            Exception: If the request fails
        """
        ...
    
    def connect_to_emqx(self) -> mqtt.Client:
        """
        Connect to EMQX MQTT broker.
        
        Returns:
            mqtt.Client: Connected MQTT client
            
        Raises:
            Exception: If connection fails
        """
        ...


class UCodeSDK:
    """
    Main UCode SDK implementation - equivalent to 'object' struct in Go.
    
    This class implements the UcodeApis interface and provides the main
    functionality for interacting with the UCode API.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the UCode SDK with configuration.
        
        Args:
            config: SDK configuration object
        """
        self._config = config
        self._session = requests.Session()
        
        # Set up default headers
        self._session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'UCode-Python-SDK/1.0.0'
        })
        
        # Add app-specific headers if available
        if config.app_id:
            self._session.headers.update({'X-App-ID': config.app_id})
        
        if config.function_name:
            self._session.headers.update({'X-Function-Name': config.function_name})
    
    def items(self, collection: str) -> ItemsI:
        """
        Items returns an interface to interact with items within a specified collection.
        Items are objects within a Collection which contain values for one or more fields.
        Each item represents a record in your database, allowing CRUD operations.
        
        Usage:
            sdk.items("collection_name").create(data).exec()
        
        This enables you to manage items in collections across databases, 
        such as MongoDB and PostgreSQL.
        
        Args:
            collection: The name of the collection to interact with
            
        Returns:
            ItemsI: Interface for items operations
        """
        from .items import APIItem as Items
        return Items(self, collection)
    
    def auth(self) -> AuthI:
        """
        Auth returns an interface for handling user authentication and authorization operations.
        Use this interface to manage user registration, login, password resets, and other
        authentication-related tasks.
        
        Usage:
            sdk.auth().register(data).exec()
        
        Supports various authentication workflows compatible with both MongoDB and PostgreSQL.
        
        Returns:
            AuthI: Interface for authentication operations
        """
        from .auth import Auth
        return Auth(self)
    
    def files(self) -> FilesI:
        """
        Files returns an interface for file management operations.
        Use this interface to upload, delete, or manage files stored on the server, allowing
        for easy integration of file-based data alongside other operations.
        
        Usage:
            sdk.files().upload("file_path").exec()
        
        Designed for compatibility with both MongoDB and PostgreSQL for consistent file management.
        
        Returns:
            FilesI: Interface for file operations
        """
        from .files import Files
        return Files(self)
    
    def function(self, path: str) -> FunctionI:
        """
        Function returns an interface for invoking server-side functions.
        This interface enables the execution of predefined or custom server functions,
        facilitating complex data processing and automation workflows.
        
        Usage:
            sdk.function("function_path").invoke(data).exec()
        
        Supported across MongoDB and PostgreSQL, providing flexibility for backend processing.
        
        Args:
            path: The path to the server function
            
        Returns:
            FunctionI: Interface for function operations
        """
        return Function(self, path)
    
    def config(self) -> Config:
        """
        Get the current configuration object.
        
        Returns:
            Config: The SDK configuration
        """
        return self._config
    
    def do_request(self, url: str, method: str, body: Any = None, 
                   headers: Optional[Dict[str, str]] = None) -> bytes:
        """
        Execute an HTTP request with the given parameters.
        
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
            json_data = body
        
        # Prepare headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # Make the request
        response = self._session.request(
            method=method.upper(),
            url=url,
            json=json_data,
            headers=request_headers,
            timeout=getattr(self._config, 'request_timeout', 30)
        )
        
        # Raise an exception for bad status codes
        response.raise_for_status()
        
        return response.content
    
    def connect_to_emqx(self) -> mqtt.Client:

        if not self._config.mqtt_broker:
            raise ValueError("MQTT broker configuration is required")
        
        # Create MQTT client (equivalent to mqtt.NewClient(opts))
        client = mqtt.Client()
        
        # Set up authentication (equivalent to opts.SetUsername/SetPassword)
        if self._config.mqtt_username:
            client.username_pw_set(
                self._config.mqtt_username, 
                self._config.mqtt_password or ""
            )
        
        # Connect to broker (equivalent to client.Connect() and token.Wait())
        try:
            # Extract host and port from broker URL if needed
            broker_host = self._config.mqtt_broker
            broker_port = 1883  # default MQTT port
            
            # Handle broker URL format (e.g., "tcp://broker.example.com:1883")
            if "://" in broker_host:
                protocol, host_port = broker_host.split("://", 1)
                if ":" in host_port:
                    broker_host, port_str = host_port.split(":", 1)
                    broker_port = int(port_str)
                else:
                    broker_host = host_port
            
            # Connect (equivalent to token.Wait() && token.Error())
            client.connect(broker_host, broker_port, 60)
            
            return client
            
        except Exception as e:
            raise Exception(f"Failed to connect to MQTT broker: {str(e)}")
    
    # Also add it as a method that matches the Go interface exactly
    def connect_to_emqx(self) -> mqtt.Client:
        """
        ConnectToEMQX - exact equivalent to Go's ConnectToEMQX() method.
        
        Returns:
            mqtt.Client: Connected MQTT client
            
        Raises:
            Exception: If connection fails
        """
        return self.connect_to_emqx()


def new(config: Config) -> UCodeSDK:
    """
    Create a new UCode SDK instance - equivalent to New() function in Go.
    
    Args:
        config: SDK configuration
        
    Returns:
        UcodeApis: New SDK instance
    """
    return UCodeSDK(config)




# For backward compatibility and convenience
UcodeAPI = UCodeSDK  # Alias
Object = UCodeSDK    # Direct equivalent to Go's 'object' struct


__all__ = [
    'UcodeApis',
    'UCodeSDK', 
    'UcodeAPI',
    'Object',
    'new',
    'do_request'
]