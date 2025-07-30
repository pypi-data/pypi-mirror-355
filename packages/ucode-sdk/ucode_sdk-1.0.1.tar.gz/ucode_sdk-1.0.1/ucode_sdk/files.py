"""
UCode Python SDK - Files Module

This module provides file management functionality,
equivalent to files.go in the original Go SDK.
"""

import json
import os
from typing import Dict, Any, Tuple, Protocol
import requests
from .models import CreateFileResponse, Response, Request, UploadFile, DeleteFile
from .config import Config


class FilesI(Protocol):
    """
    FilesI interface - equivalent to FilesI interface in Go.
    """
    
    def upload(self, file_path: str) -> 'UploadFileBuilder':
        """
        Upload is a function that uploads a file to the server.

        Works for [Mongo, Postgres]

        sdk.files().upload("file_path").exec()

        Use this method to store a file and obtain its metadata for retrieval or management.
        """
        ...
    
    def delete(self, file_id: str) -> 'DeleteFileBuilder':
        """
        Delete is a function that deletes a file from the server.

        Works for [Mongo, Postgres]

        sdk.files().delete("file_id").exec()

        This method removes a file based on its unique identifier, allowing for clean file management.
        """
        ...


class APIFiles:
    """
    APIFiles class - equivalent to APIFiles struct in Go.
    """
    
    def __init__(self, sdk_instance):
        """
        Initialize APIFiles with SDK instance.
        
        Args:
            sdk_instance: The main SDK instance
        """
        self.config = sdk_instance.config()
        self._sdk = sdk_instance
    
    def upload(self, file_path: str) -> 'UploadFileBuilder':
        """
        Upload is a function that uploads a file to the server.

        Works for [Mongo, Postgres]

        sdk.files().upload("file_path").exec()

        Use this method to store a file and obtain its metadata for retrieval or management.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            UploadFileBuilder: Builder for upload operation
        """
        return UploadFileBuilder(
            config=self.config,
            path=file_path
        )
    
    def delete(self, file_id: str) -> 'DeleteFileBuilder':
        """
        Delete is a function that deletes a file from the server.

        Works for [Mongo, Postgres]

        sdk.files().delete("file_id").exec()

        This method removes a file based on its unique identifier, allowing for clean file management.
        
        Args:
            file_id: ID of the file to delete
            
        Returns:
            DeleteFileBuilder: Builder for delete operation
        """
        return DeleteFileBuilder(
            config=self.config,
            id=file_id
        )

class UploadFileBuilder:
    """
    UploadFileBuilder class - equivalent to UploadFile struct operations in Go.
    """
    
    def __init__(self, config: Config, path: str):
        """
        Initialize UploadFileBuilder.
        
        Args:
            config: SDK configuration
            path: File path to upload
        """
        self.config = config
        self.path = path
    
    def exec(self) -> Tuple[CreateFileResponse, Response, Exception]:
        """
        Execute the file upload request.
        
        Returns:
            Tuple of (CreateFileResponse, Response, Exception)
        """
        response = Response(
            status="done",
            error="",
            data={}
        )
        
        url = f"{self.config.base_url}/v1/files/folder_upload?folder_name=Media"
        
        try:
            # Check if file exists
            if not os.path.exists(self.path):
                raise FileNotFoundError(f"File not found: {self.path}")
            
            # Prepare headers
            app_id = self.config.app_id
            headers = {
                "authorization": "API-KEY",
                "X-API-KEY": app_id,
            }
            
            # Open and read the file
            with open(self.path, 'rb') as file:
                file_name = os.path.basename(self.path)
                files = {'file': (file_name, file, 'application/octet-stream')}
                
                # Make the request using do_file_request
                create_file_bytes = do_file_request(
                    url=url,
                    method="POST",
                    headers=headers,
                    files=files
                )
            
            # Parse response
            create_file_dict = json.loads(create_file_bytes.decode('utf-8'))
            created_object = CreateFileResponse(**create_file_dict)
            
            return created_object, response, None
            
        except FileNotFoundError as err:
            response.data = {
                "description": self.path,
                "message": "can't open file by path",
                "error": str(err)
            }
            response.status = "error"
            return CreateFileResponse(), response, err
            
        except Exception as err:
            response.data = {
                "description": str(create_file_bytes) if 'create_file_bytes' in locals() else "",
                "message": "Can't send request",
                "error": str(err)
            }
            response.status = "error"
            return CreateFileResponse(), response, err


class DeleteFileBuilder:
    """
    DeleteFileBuilder class - equivalent to DeleteFile struct operations in Go.
    """
    
    def __init__(self, config: Config, id: str):
        """
        Initialize DeleteFileBuilder.
        
        Args:
            config: SDK configuration
            id: File ID to delete
        """
        self.config = config
        self.id = id
    
    def exec(self) -> Tuple[Response, Exception]:
        """
        Execute the file delete request.
        
        Returns:
            Tuple of (Response, Exception)
        """
        from .helper import do_request
        
        response = Response(status="done", error="", data={})
        url = f"{self.config.base_url}/v1/files/{self.id}"
        
        app_id = self.config.app_id
        headers = {
            "authorization": "API-KEY",
            "X-API-KEY": app_id,
        }
        
        try:
            do_request(
                url=url,
                method="DELETE",
                body=Request(data={}, is_cached=False).data,
                headers=headers
            )
            
            return response, None
            
        except Exception as err:
            response.data = {
                "message": "Error while deleting file",
                "error": str(err)
            }
            response.status = "error"
            return response, err


def do_file_request(url: str, method: str, headers: Dict[str, str], files: Dict[str, Any]) -> bytes:
    """
    Execute a file upload HTTP request - equivalent to DoFileRequest() in Go.
    
    This function handles multipart file uploads with proper content-type headers.
    
    Args:
        url: The URL to make the request to
        method: HTTP method (should be POST for file uploads)
        headers: HTTP headers to include
        files: Files to upload (in requests format)
        
    Returns:
        bytes: Response body as bytes
        
    Raises:
        requests.RequestException: If the request fails
    """
    # Create HTTP client session
    session = requests.Session()
    
    # Prepare request headers (don't set Content-Type, requests will handle it for multipart)
    request_headers = {}
    if headers:
        request_headers.update(headers)
    
    # Make the request with file upload
    response = session.request(
        method=method.upper(),
        url=url,
        files=files,
        headers=request_headers,
        timeout=30
    )
    
    # Raise an exception for bad status codes
    response.raise_for_status()
    
    return response.content


# Aliases for compatibility
Files = APIFiles
FilesInterface = FilesI


__all__ = [
    'FilesI',
    'APIFiles',
    'Files',
    'FilesInterface',
    'UploadFileBuilder',
    'DeleteFileBuilder',
    'do_file_request'
]