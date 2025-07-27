"""Proxy router with permission validation"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.auth.schemas import PermissionSchema
from src.backends import PermissionChecker, get_db_session
from src.proxy.service import proxy_service

proxy_router = APIRouter(tags=["proxy"])


# Permission definitions for different proxy endpoints
PROXY_PERMISSIONS = {
    # Example permissions - adjust according to your needs
    "read": PermissionSchema(module="procurement", model="supplier", action="view"),
    "write": [
        PermissionSchema(module="procurement", model="supplier", action="add"),
        PermissionSchema(module="procurement", model="supplier", action="edit"),
    ],
}


def get_permission_checker(permission_type: str = "read"):
    """Get permission checker for specific permission type"""
    if permission_type not in PROXY_PERMISSIONS:
        raise ValueError(f"Unknown permission type: {permission_type}")

    return PermissionChecker(PROXY_PERMISSIONS[permission_type])


@proxy_router.api_route(
    "/{service_name}/{path:path}",
    methods=["GET"],
    summary="Proxy GET requests to external service",
)
async def proxy_get(
    service_name: str,
    path: str,
    request: Request,
    current_user: UserModel = Depends(get_permission_checker("read")),
    db_session: Session = Depends(get_db_session),
):
    """
    Proxy GET requests to external service with permission validation.
    Requires 'read' permission for proxy.external_service.
    """
    return await proxy_service.proxy_get_request(
        service_name, path, request, current_user
    )


@proxy_router.api_route(
    "/{service_name}/{path:path}",
    methods=["POST"],
    summary="Proxy POST requests to external service",
)
async def proxy_post(
    service_name: str,
    path: str,
    request: Request,
    current_user: UserModel = Depends(get_permission_checker("write")),
    db_session: Session = Depends(get_db_session),
):
    """
    Proxy POST requests to external service with permission validation.
    Requires 'write' permission for proxy.external_service.
    """
    return await proxy_service.proxy_post_request(
        service_name, path, request, current_user
    )


@proxy_router.api_route(
    "/{service_name}/{path:path}",
    methods=["PUT"],
    summary="Proxy PUT requests to external service",
)
async def proxy_put(
    service_name: str,
    path: str,
    request: Request,
    current_user: UserModel = Depends(get_permission_checker("write")),
    db_session: Session = Depends(get_db_session),
):
    """
    Proxy PUT requests to external service with permission validation.
    Requires 'write' permission for proxy.external_service.
    """
    return await proxy_service.proxy_put_request(
        service_name, path, request, current_user
    )


@proxy_router.api_route(
    "/{service_name}/{path:path}",
    methods=["PATCH"],
    summary="Proxy PATCH requests to external service",
)
async def proxy_patch(
    service_name: str,
    path: str,
    request: Request,
    current_user: UserModel = Depends(get_permission_checker("write")),
    db_session: Session = Depends(get_db_session),
):
    """
    Proxy PATCH requests to external service with permission validation.
    Requires 'write' permission for proxy.external_service.
    """
    return await proxy_service.proxy_patch_request(
        service_name, path, request, current_user
    )


@proxy_router.get(
    "/{service_name}/health",
    summary="Check proxy and external service health",
)
async def proxy_health(
    service_name: str,
    current_user: UserModel = Depends(get_permission_checker("read")),
    db_session: Session = Depends(get_db_session),
):
    """
    Check the health of the proxy service and external service connection.
    Requires 'read' permission for proxy.external_service.
    """
    return await proxy_service.proxy_health_check(service_name, current_user)
