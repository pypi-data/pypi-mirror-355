"""
UCode Python SDK - Configuration Module

This module provides the configuration class,
equivalent to config.go in the original Go SDK.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """
    Configuration class for UCode SDK - equivalent to Config struct in Go.
    
    This is a direct 1:1 mapping of the Go struct fields.
    """
    
    app_id: str = ""
    base_url: str = ""
    function_name: str = ""
    project_id: str = ""
    request_timeout: float = 0.0  # seconds (equivalent to time.Duration in Go)
    base_auth_url: str = ""
    mqtt_broker: str = ""
    mqtt_username: str = ""
    mqtt_password: str = ""


__all__ = ['Config']