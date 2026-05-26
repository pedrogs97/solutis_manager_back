"""Proxy router with permission validation"""

from typing import Generator, Union

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlalchemy.orm import Session, selectinload

from src.auth.models import GroupModel, TokenModel, UserModel
from src.auth.schemas import PermissionSchema
from src.backends import (
    PermissionChecker,
    get_db_session,
    oauth2_bearer,
    token_is_valid,
)
from src.config import NOT_ALLOWED
from src.proxy.service import INSUFFICIENT_PERMISSIONS_MSG, proxy_service

proxy_router = APIRouter(prefix="/proxy", tags=["proxy"])


PROXY_PERMISSIONS = {
    "read": [
        PermissionSchema(module="procurement", model="supplier", action="view"),
        PermissionSchema(module="report", model="report", action="view"),
    ],
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


def get_proxy_authenticated_user(
    token: str = Depends(oauth2_bearer),
    db_session: Session = Depends(get_db_session),
) -> Generator[Union[UserModel, None], None, None]:
    """Authenticate proxy requests using opaque access token."""
    try:
        token_db = (
            db_session.query(TokenModel).filter(TokenModel.token == token).first()
        )
        if not token_is_valid(token_db):
            logger.warning("Invalid token")
            yield None
            return

        user = (
            db_session.query(UserModel)
            .options(
                selectinload(UserModel.group).selectinload(GroupModel.permissions),
                selectinload(UserModel.employee),
            )
            .filter(UserModel.id == token_db.user_id)
            .first()
        )
        yield user
    finally:
        db_session.close()


def authorize_proxy_access(
    current_user: Union[UserModel, None],
    permission_type: str,
) -> UserModel:
    """Authorize proxy request and distinguish auth vs permission failures."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=NOT_ALLOWED,
        )

    permission_checker = get_permission_checker(permission_type)
    if not permission_checker.has_permissions(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=INSUFFICIENT_PERMISSIONS_MSG,
        )

    return current_user


@proxy_router.api_route(
    "/{service_name}/{path:path}",
    methods=["GET"],
    summary="Proxy GET requests to external service",
)
async def proxy_get(
    service_name: str,
    path: str,
    request: Request,
    current_user: Union[UserModel, None] = Depends(get_proxy_authenticated_user),
):
    """
    Proxy GET requests to external service with permission validation.
    Requires 'read' permission for proxy.external_service.
    """
    authorized_user = authorize_proxy_access(current_user, "read")
    return await proxy_service.proxy_get_request(
        service_name, path, request, authorized_user
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
    current_user: Union[UserModel, None] = Depends(get_proxy_authenticated_user),
):
    """
    Proxy POST requests to external service with permission validation.
    Requires 'write' permission for proxy.external_service.
    """
    authorized_user = authorize_proxy_access(current_user, "write")
    return await proxy_service.proxy_post_request(
        service_name, path, request, authorized_user
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
    current_user: Union[UserModel, None] = Depends(get_proxy_authenticated_user),
):
    """
    Proxy PUT requests to external service with permission validation.
    Requires 'write' permission for proxy.external_service.
    """
    authorized_user = authorize_proxy_access(current_user, "write")
    return await proxy_service.proxy_put_request(
        service_name, path, request, authorized_user
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
    current_user: Union[UserModel, None] = Depends(get_proxy_authenticated_user),
):
    """
    Proxy PATCH requests to external service with permission validation.
    Requires 'write' permission for proxy.external_service.
    """
    authorized_user = authorize_proxy_access(current_user, "write")
    return await proxy_service.proxy_patch_request(
        service_name, path, request, authorized_user
    )


@proxy_router.api_route(
    "/{service_name}/{path:path}",
    methods=["DELETE"],
    summary="Proxy DELETE requests to external service",
)
async def proxy_delete(
    service_name: str,
    path: str,
    request: Request,
    current_user: Union[UserModel, None] = Depends(get_proxy_authenticated_user),
):
    """
    Proxy DELETE requests to external service with permission validation.
    Requires 'write' permission for proxy.external_service.
    """
    authorized_user = authorize_proxy_access(current_user, "write")
    return await proxy_service.proxy_delete_request(
        service_name, path, request, authorized_user
    )


@proxy_router.get(
    "/{service_name}/health",
    summary="Check proxy and external service health",
)
async def proxy_health(
    service_name: str,
    current_user: Union[UserModel, None] = Depends(get_proxy_authenticated_user),
):
    """
    Check the health of the proxy service and external service connection.
    Requires 'read' permission for proxy.external_service.
    """
    authorized_user = authorize_proxy_access(current_user, "read")
    return await proxy_service.proxy_health_check(service_name, authorized_user)
