"""Proxy service for external API with permission validation"""

import asyncio
import logging
from typing import Any, Dict, Optional, Union

import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import Response

from src.auth.models import UserModel
from src.proxy.config import (
    EXTERNAL_SERVICE_RETRY_ATTEMPTS,
    EXTERNAL_SERVICE_TIMEOUT,
    FORWARD_HEADERS,
    get_external_service_url,
    is_valid_service,
)

logger = logging.getLogger(__name__)

# Constants
INSUFFICIENT_PERMISSIONS_MSG = "Insufficient permissions"
DEFAULT_MEDIA_TYPE = "application/json"
PROXY_ERROR_PREFIX = "Proxy error: "


class ProxyService:
    """Service for proxying requests to external API with permission validation"""

    def __init__(self):
        self.timeout = EXTERNAL_SERVICE_TIMEOUT
        self.retry_attempts = EXTERNAL_SERVICE_RETRY_ATTEMPTS

    def _filter_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Filter headers to forward only allowed ones"""
        filtered_headers = {}
        if headers:
            for header_name in FORWARD_HEADERS:
                if header_name in headers:
                    filtered_headers[header_name] = headers[header_name]
        return filtered_headers

    def _handle_request_errors(self, attempt: int, url: str, error: Exception):
        """Handle request errors with appropriate exceptions"""
        if isinstance(error, httpx.TimeoutException):
            logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
            if attempt == self.retry_attempts - 1:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="External service timeout",
                )
        elif isinstance(error, httpx.ConnectError):
            logger.error(f"Connection error on attempt {attempt + 1} for {url}")
            if attempt == self.retry_attempts - 1:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to connect to external service",
                )
        else:
            logger.error(
                f"Unexpected error on attempt {attempt + 1} for {url}: {error}"
            )
            if attempt == self.retry_attempts - 1:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="External service error",
                )

    async def _make_single_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        filtered_headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
    ) -> httpx.Response:
        """Make a single HTTP request"""
        return await client.request(
            method=method,
            url=url,
            headers=filtered_headers,
            params=params,
            json=json_data,
            data=data,
        )

    async def _make_request(
        self,
        method: str,
        service_name: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
    ) -> httpx.Response:
        """Make HTTP request to external service with retry logic"""

        if not is_valid_service(service_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid service name: {service_name}",
            )

        url = get_external_service_url(service_name, path)
        filtered_headers = self._filter_headers(headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.retry_attempts):
                try:
                    logger.info(
                        f"Proxying {method} request to {url} (attempt {attempt + 1})"
                    )

                    response = await self._make_single_request(
                        client, method, url, filtered_headers, params, json_data, data
                    )

                    logger.info(
                        f"External service responded with status {response.status_code}"
                    )
                    return response

                except Exception as error:
                    self._handle_request_errors(attempt, url, error)

                    # Wait before retry (exponential backoff)
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(2 ** attempt)

        # This should never be reached due to the error handling above
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to complete request after all retry attempts",
        )

    async def get(
        self,
        service_name: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Proxy GET request to external service"""
        return await self._make_request("GET", service_name, path, headers, params)

    async def post(
        self,
        service_name: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
    ) -> httpx.Response:
        """Proxy POST request to external service"""
        return await self._make_request(
            "POST", service_name, path, headers, json_data=json_data, data=data
        )

    async def put(
        self,
        service_name: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
    ) -> httpx.Response:
        """Proxy PUT request to external service"""
        return await self._make_request(
            "PUT", service_name, path, headers, json_data=json_data, data=data
        )

    async def patch(
        self,
        service_name: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
    ) -> httpx.Response:
        """Proxy PATCH request to external service"""
        return await self._make_request(
            "PATCH", service_name, path, headers, json_data=json_data, data=data
        )

    async def delete(
        self,
        service_name: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Proxy DELETE request to external service"""
        return await self._make_request("DELETE", service_name, path, headers, params)

    def validate_user_permissions(self, current_user: UserModel):
        """Validate user permissions and raise exception if insufficient"""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=INSUFFICIENT_PERMISSIONS_MSG,
            )

    def create_response(self, response: httpx.Response) -> Response:
        """Create FastAPI Response from httpx Response"""
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type", DEFAULT_MEDIA_TYPE),
        )

    async def handle_request_body(self, request: Request):
        """Extract and handle request body based on content type"""
        headers = dict(request.headers)

        try:
            if headers.get("content-type", "").startswith(DEFAULT_MEDIA_TYPE):
                json_data = await request.json()
                data = None
            else:
                json_data = None
                data = await request.body()
        except Exception:
            json_data = None
            data = await request.body()

        return headers, json_data, data

    async def proxy_get_request(
        self,
        service_name: str,
        path: str,
        request: Request,
        current_user: UserModel,
    ) -> Response:
        """Handle GET proxy request with validation"""
        self.validate_user_permissions(current_user)

        # Extract headers and query parameters
        headers = dict(request.headers)
        params = dict(request.query_params)

        try:
            response = await self.get(
                service_name, path, headers=headers, params=params
            )
            return self.create_response(response)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PROXY_ERROR_PREFIX}{str(e)}",
            )

    async def proxy_post_request(
        self,
        service_name: str,
        path: str,
        request: Request,
        current_user: UserModel,
    ) -> Response:
        """Handle POST proxy request with validation"""
        self.validate_user_permissions(current_user)

        headers, json_data, data = await self.handle_request_body(request)

        try:
            response = await self.post(
                service_name, path, headers=headers, json_data=json_data, data=data
            )
            return self.create_response(response)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PROXY_ERROR_PREFIX}{str(e)}",
            )

    async def proxy_put_request(
        self,
        service_name: str,
        path: str,
        request: Request,
        current_user: UserModel,
    ) -> Response:
        """Handle PUT proxy request with validation"""
        self.validate_user_permissions(current_user)

        headers, json_data, data = await self.handle_request_body(request)

        try:
            response = await self.put(
                service_name, path, headers=headers, json_data=json_data, data=data
            )
            return self.create_response(response)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PROXY_ERROR_PREFIX}{str(e)}",
            )

    async def proxy_patch_request(
        self,
        service_name: str,
        path: str,
        request: Request,
        current_user: UserModel,
    ) -> Response:
        """Handle PATCH proxy request with validation"""
        self.validate_user_permissions(current_user)

        headers, json_data, data = await self.handle_request_body(request)

        try:
            response = await self.patch(
                service_name, path, headers=headers, json_data=json_data, data=data
            )
            return self.create_response(response)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PROXY_ERROR_PREFIX}{str(e)}",
            )

    async def proxy_delete_request(
        self,
        service_name: str,
        path: str,
        request: Request,
        current_user: UserModel,
    ) -> Response:
        """Handle DELETE proxy request with validation"""
        self.validate_user_permissions(current_user)

        # Extract headers and query parameters
        headers = dict(request.headers)
        params = dict(request.query_params)

        try:
            response = await self.delete(
                service_name, path, headers=headers, params=params
            )
            return self.create_response(response)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PROXY_ERROR_PREFIX}{str(e)}",
            )

    async def proxy_health_check(
        self, service_name: str, current_user: UserModel
    ) -> Dict[str, Any]:
        """Handle health check request with validation"""
        self.validate_user_permissions(current_user)

        try:
            response = await self.get(service_name, "health")

            return {
                "proxy_status": "healthy",
                "service_name": service_name,
                "external_service_status": (
                    "healthy" if response.status_code < 500 else "unhealthy"
                ),
                "external_service_response_code": response.status_code,
            }

        except HTTPException as e:
            return {
                "proxy_status": "healthy",
                "service_name": service_name,
                "external_service_status": "unhealthy",
                "error": e.detail,
            }
        except Exception as e:
            return {
                "proxy_status": "healthy",
                "service_name": service_name,
                "external_service_status": "unknown",
                "error": str(e),
            }


# Singleton instance
proxy_service = ProxyService()
