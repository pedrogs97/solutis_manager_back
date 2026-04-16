"""Proxy service for external API with permission validation"""

import asyncio
import json
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import Response
from loguru import logger
from src.auth.models import UserModel
from src.config import NOT_ALLOWED
from src.proxy.config import (EXTERNAL_SERVICE_RETRY_ATTEMPTS,
                              EXTERNAL_SERVICE_TIMEOUT, FORWARD_HEADERS,
                              get_external_service_url, is_valid_service)

# Constants
INSUFFICIENT_PERMISSIONS_MSG = "Insufficient permissions"
DEFAULT_MEDIA_TYPE = "application/json"
PROXY_ERROR_PREFIX = "Proxy error: "
HTTP_ERROR_LOG_MSG = "HTTP error occurred: {}"
AUTH_CONTEXT_HEADERS = (
    "x-authenticated-user-id",
    "x-authenticated-user-email",
    "x-authenticated-user-full-name",
    "x-authenticated-user-group",
)


class ProxyService:
    """Service for proxying requests to external API with permission validation"""

    def __init__(self):
        self.timeout = EXTERNAL_SERVICE_TIMEOUT
        self.retry_attempts = EXTERNAL_SERVICE_RETRY_ATTEMPTS

    def _filter_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Filter headers to forward only allowed ones"""
        filtered_headers = {}
        if headers:
            normalized_headers = {key.lower(): value for key, value in headers.items()}
            for header_name in FORWARD_HEADERS:
                if header_name in normalized_headers:
                    filtered_headers[header_name] = normalized_headers[header_name]
        return filtered_headers

    def _build_authenticated_headers(self, current_user: UserModel) -> Dict[str, str]:
        """Build authenticated user headers injected by the trusted proxy.

        Values are URL-encoded (RFC 5987) so non-ASCII characters
        (common in Portuguese names) survive the ASCII-only HTTP header
        transport.  The downstream service must URL-decode them.
        """
        full_name = (
            current_user.employee.full_name
            if current_user.employee and current_user.employee.full_name
            else "Usuario"
        )
        group_name = current_user.group.name if current_user.group else ""
        return {
            "x-authenticated-user-id": str(current_user.id),
            "x-authenticated-user-email": quote(
                str(current_user.email or "").strip(), safe="@."
            ),
            "x-authenticated-user-full-name": quote(
                str(full_name).strip(), safe=""
            ),
            "x-authenticated-user-group": quote(
                str(group_name).strip(), safe=""
            ),
        }

    def _prepare_proxy_headers(
        self, request_headers: Dict[str, str], current_user: UserModel
    ) -> Dict[str, str]:
        """Prepare headers forwarded to upstream service."""
        headers = dict(request_headers)
        for header_name in AUTH_CONTEXT_HEADERS:
            headers.pop(header_name, None)
        headers.update(self._build_authenticated_headers(current_user))
        return headers

    def _handle_request_errors(self, attempt: int, url: str, error: Exception):
        """Handle request errors with appropriate exceptions"""
        if isinstance(error, httpx.TimeoutException):
            logger.warning("Timeout on attempt {} for {}", attempt + 1, url)
            if attempt == self.retry_attempts - 1:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="External service timeout",
                )
        elif isinstance(error, httpx.ConnectError):
            logger.error("Connection error on attempt {} for {}", attempt + 1, url)
            if attempt == self.retry_attempts - 1:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to connect to external service",
                )
        else:
            logger.exception(
                "Unexpected error on attempt {} for {}: {}",
                attempt + 1,
                url,
                error,
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
                        "Proxying {} request to {} (attempt {})",
                        method,
                        url,
                        attempt + 1,
                    )

                    response = await self._make_single_request(
                        client, method, url, filtered_headers, params, json_data, data
                    )

                    logger.info(
                        "External service responded with status {}",
                        response.status_code,
                    )
                    return response

                except Exception as error:
                    self._handle_request_errors(attempt, url, error)

                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(2 ** attempt)

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
        """Validate authentication context before proxying request."""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=NOT_ALLOWED,
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
        content_type = str(headers.get("content-type", "")).lower()
        raw_body = await request.body()

        if not raw_body:
            return headers, None, None

        try:
            if (
                content_type.startswith(DEFAULT_MEDIA_TYPE)
                or content_type.endswith("+json")
            ):
                return headers, json.loads(raw_body.decode("utf-8")), None
        except (ValueError, UnicodeDecodeError):
            logger.warning(
                "Failed to parse JSON body for content-type '{}', forwarding raw body",
                content_type,
            )

        return headers, None, raw_body

    async def proxy_get_request(
        self,
        service_name: str,
        path: str,
        request: Request,
        current_user: UserModel,
    ) -> Response:
        """Handle GET proxy request with validation"""
        self.validate_user_permissions(current_user)

        headers = self._prepare_proxy_headers(dict(request.headers), current_user)
        params = dict(request.query_params)

        try:
            response = await self.get(
                service_name, path, headers=headers, params=params
            )
            return self.create_response(response)

        except HTTPException as e:
            logger.error(HTTP_ERROR_LOG_MSG, e.detail)
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PROXY_ERROR_PREFIX}{str(e)}",
            ) from e

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
        headers = self._prepare_proxy_headers(headers, current_user)

        try:
            response = await self.post(
                service_name, path, headers=headers, json_data=json_data, data=data
            )
            return self.create_response(response)

        except HTTPException as e:
            logger.error(HTTP_ERROR_LOG_MSG, e.detail)
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PROXY_ERROR_PREFIX}{str(e)}",
            ) from e

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
        headers = self._prepare_proxy_headers(headers, current_user)

        try:
            response = await self.put(
                service_name, path, headers=headers, json_data=json_data, data=data
            )
            return self.create_response(response)

        except HTTPException as e:
            logger.error(HTTP_ERROR_LOG_MSG, e.detail)
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PROXY_ERROR_PREFIX}{str(e)}",
            ) from e

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
        headers = self._prepare_proxy_headers(headers, current_user)

        try:
            response = await self.patch(
                service_name, path, headers=headers, json_data=json_data, data=data
            )
            return self.create_response(response)

        except HTTPException as e:
            logger.error(HTTP_ERROR_LOG_MSG, e.detail)
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PROXY_ERROR_PREFIX}{str(e)}",
            ) from e

    async def proxy_delete_request(
        self,
        service_name: str,
        path: str,
        request: Request,
        current_user: UserModel,
    ) -> Response:
        """Handle DELETE proxy request with validation"""
        self.validate_user_permissions(current_user)

        headers = self._prepare_proxy_headers(dict(request.headers), current_user)
        params = dict(request.query_params)

        try:
            response = await self.delete(
                service_name, path, headers=headers, params=params
            )
            return self.create_response(response)

        except HTTPException as e:
            logger.error(HTTP_ERROR_LOG_MSG, e.detail)
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{PROXY_ERROR_PREFIX}{str(e)}",
            ) from e

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


proxy_service = ProxyService()
