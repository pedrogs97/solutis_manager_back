"""Auth router"""
from typing import Optional
from fastapi import Depends, APIRouter, Response, status, Query
from fastapi.responses import JSONResponse
from fastapi_pagination import Page
from sqlalchemy.orm import Session
from app.auth.schemas import (
    NewUserSchema,
    LoginSchema,
    UserSerializer,
    UserUpdateSchema,
    NewRoleSchema,
    RoleSerializer,
    PermissionSerializer,
)
from app.auth.service import UserSerivce, RoleService, PermissionService
from app.backends import (
    get_user,
    get_user_token,
    token_exception,
    logout_user,
    oauth2_bearer,
    PermissionChecker,
    get_db_session,
)
from app.auth.config import (
    PAGINATION_NUMBER,
    MAX_PAGINATION_NUMBER,
    PAGE_NUMBER_DESCRIPTION,
    PAGE_SIZE_DESCRIPTION,
    NOT_ALLOWED,
)


auth_router = APIRouter(prefix="/auth", tags=["Auth"])

user_service = UserSerivce()

role_service = RoleService()

permission_serivce = PermissionService()


@auth_router.post("/login/")
async def login_route(
    data: LoginSchema,
    db_session: Session = Depends(get_db_session),
):
    """Login user route"""
    user = get_user(data.username, data.password, db_session)
    if not user:
        raise token_exception()
    return JSONResponse(
        content=get_user_token(user, db_session), status_code=status.HTTP_200_OK
    )


@auth_router.post("/logout/")
async def logout_route(
    token: str = Depends(oauth2_bearer), db_session: Session = Depends(get_db_session)
):
    """Logout user route"""
    logout_user(token, db_session)
    return JSONResponse(content={"message": "logout"}, status_code=status.HTTP_200_OK)


@auth_router.post(
    "/users/", response_model=UserSerializer, description="Creates new user"
)
async def create_user_route(
    data: NewUserSchema,
    authenticated: bool = Depends(
        PermissionChecker({"module": "people", "model": "user", "method": "add"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """New user route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = user_service.create_user(data, db_session)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_201_CREATED
    )


@auth_router.get(
    "/users/",
    response_model=Page[UserSerializer],
    description="Retrie list of users. Can apply filters",
)
async def get_list_user_route(
    authenticated: bool = Depends(
        PermissionChecker({"module": "people", "model": "user", "method": "view"})
    ),
    search: str = "",
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    active: bool = Query(True, description="Active user"),
    staff: Optional[bool] = Query(None, description="Staff user"),
    db_session: Session = Depends(get_db_session),
):
    """List users route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    return user_service.get_users(db_session, page, size, search, active, staff)


@auth_router.patch(
    "/users/{user_id}/",
    response_model=UserSerializer,
    description="Updates an existing user",
)
async def update_user_route(
    data: UserUpdateSchema,
    user_id: int,
    authenticated: bool = Depends(
        PermissionChecker({"module": "people", "model": "user", "method": "edit"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Update user route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = user_service.update_user(db_session, user_id, data)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@auth_router.get(
    "/users/{user_id}/",
    response_model=UserSerializer,
    description="Retrives an existing user",
)
async def get_user_route(
    user_id: int,
    authenticated: bool = Depends(
        PermissionChecker({"module": "people", "model": "user", "method": "view"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Get user route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = user_service.get_user(user_id, db_session)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@auth_router.post(
    "/roles/", response_model=RoleSerializer, description="Creates a new role"
)
async def create_role_route(
    data: NewRoleSchema,
    authenticated: bool = Depends(
        PermissionChecker({"module": "auth", "model": "role", "method": "add"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """New role route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = role_service.create_role(data, db_session)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_201_CREATED
    )


@auth_router.get(
    "/roles/",
    response_model=Page[RoleSerializer],
    description="Retrie list of roles. Can apply filters",
)
async def get_list_role_route(
    authenticated: bool = Depends(
        PermissionChecker({"module": "auth", "model": "role", "method": "view"})
    ),
    search: str = "",
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
):
    """List roles route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    return role_service.get_roles(db_session, page, size, search)


@auth_router.patch(
    "/roles/{role_id}/",
    response_model=RoleSerializer,
    description="Updates an existing role",
)
async def update_role_route(
    data: NewRoleSchema,
    user_id: int,
    authenticated: bool = Depends(
        PermissionChecker({"module": "auth", "model": "role", "method": "edit"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Update role route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = role_service.update_role(db_session, user_id, data)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@auth_router.get(
    "/roles/{role_id}/",
    response_model=RoleSerializer,
    description="Retrives an existing role",
)
async def get_role_route(
    role_id: int,
    authenticated: bool = Depends(
        PermissionChecker({"module": "auth", "model": "role", "method": "view"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Get role route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = role_service.get_role(role_id, db_session)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@auth_router.get(
    "/permissions/",
    response_model=Page[PermissionSerializer],
    description="Retrie list of permissions. Can apply filters",
)
async def get_list_permission_route(
    authenticated: bool = Depends(
        PermissionChecker({"module": "auth", "model": "permission", "method": "view"})
    ),
    search: str = "",
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
):
    """List permissions route"""
    if not authenticated:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    return permission_serivce.get_permissions(db_session, page, size, search)
