"""Proxy service configuration and settings"""

import os
from typing import Dict, Optional

# Service configurations from environment variables
SERVICE_HOSTS = {
    "procurement": os.getenv("PROCUREMENT_SERVICE_HOST", "http://localhost:8001/api"),
    "default": os.getenv("EXTERNAL_SERVICE_HOST", "http://localhost:8001"),  # fallback
}

EXTERNAL_SERVICE_TIMEOUT = int(os.getenv("EXTERNAL_SERVICE_TIMEOUT", "30"))
EXTERNAL_SERVICE_RETRY_ATTEMPTS = int(os.getenv("EXTERNAL_SERVICE_RETRY_ATTEMPTS", "3"))
PROXY_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Headers to forward to external service
FORWARD_HEADERS = [
    "authorization",
    "content-type",
    "accept",
    "user-agent",
    "x-requested-with",
]


def get_service_host(service_name: str) -> str:
    """Get service host URL for specific service"""
    return SERVICE_HOSTS.get(service_name, SERVICE_HOSTS["default"])


def get_external_service_url(service_name: str, path: str = "") -> str:
    """Get full URL for external service endpoint"""
    base_url = get_service_host(service_name).rstrip("/")
    path = path.lstrip("/") if path else ""
    return f"{base_url}/{path}" if path else base_url


def is_valid_service(service_name: str) -> bool:
    """Check if service name is valid"""
    return service_name in SERVICE_HOSTS or service_name == "default"
