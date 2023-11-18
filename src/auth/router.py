"""Auth router"""
from typing import Optional, Union

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm as LoginSchema
from fastapi_pagination import Page
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.auth.schemas import (NewPasswordSchema, NewRoleSchema, NewUserSchema,
                              PermissionSerializerSchema, RoleSerializerSchema,
                              UserChangePasswordSchema, UserSerializerSchema,
                              UserUpdateSchema)
from src.auth.service import PermissionService, RoleService, UserSerivce
from src.backends import (PermissionChecker, get_db_session, get_user,
                          get_user_token, logout_user, oauth2_bearer,
                          token_exception)
from src.config import (MAX_PAGINATION_NUMBER, NOT_ALLOWED,
                        PAGE_NUMBER_DESCRIPTION, PAGE_SIZE_DESCRIPTION,
                        PAGINATION_NUMBER)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

user_service = UserSerivce()

role_service = RoleService()

permission_serivce = PermissionService()


@auth_router.post("/login/")
async def login_route(
    data: LoginSchema = Depends(),
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
    "/users/", response_model=UserSerializerSchema, description="Creates new user"
)
async def post_create_user_route(
    data: NewUserSchema,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "auth", "model": "user", "action": "add"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """New user route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = user_service.create_user(data, db_session, authenticated_user)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_201_CREATED
    )


@auth_router.get(
    "/users/",
    response_model=Page[UserSerializerSchema],
    description="Retrie list of users. Can apply filters",
)
async def get_list_user_route(
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "auth", "model": "user", "action": "view"})
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
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    return user_service.get_users(db_session, page, size, search, active, staff)


@auth_router.patch(
    "/users/{user_id}/",
    response_model=UserSerializerSchema,
    description="Updates an existing user",
)
async def update_user_route(
    data: UserUpdateSchema,
    user_id: int,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "auth", "model": "user", "action": "edit"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Update user route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = user_service.update_user(
        db_session, user_id, data, authenticated_user)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@auth_router.patch(
    "/users/change_password/",
    description="Updates a user's password",
)
async def update_user_password_route(
    data: UserChangePasswordSchema,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "auth", "model": "user", "action": "edit"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Update user's password route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    user_service.update_password(data, db_session, authenticated_user)
    return JSONResponse("", status_code=status.HTTP_200_OK)


@auth_router.put("/users/{user_id}/")
async def put_update_user_route():
    """Update user Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@auth_router.get(
    "/users/{user_id}/",
    response_model=UserSerializerSchema,
    description="Retrives an existing user",
)
async def get_user_route(
    user_id: int,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "auth", "model": "user", "action": "view"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Get user route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = user_service.get_user(user_id, db_session)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@auth_router.post(
    "/roles/", response_model=RoleSerializerSchema, description="Creates a new role"
)
async def post_create_role_route(
    data: NewRoleSchema,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "auth", "model": "role", "action": "add"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """New role route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = role_service.create_role(data, db_session, authenticated_user)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_201_CREATED
    )


@auth_router.get(
    "/roles/",
    response_model=Page[RoleSerializerSchema],
    description="Retrie list of roles. Can apply filters",
)
async def get_list_role_route(
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "auth", "model": "role", "action": "view"})
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
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    return role_service.get_roles(db_session, page, size, search)


@auth_router.patch(
    "/roles/{role_id}/",
    response_model=RoleSerializerSchema,
    description="Updates an existing role",
)
async def update_role_route(
    data: NewRoleSchema,
    role_id: int,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "auth", "model": "role", "action": "edit"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Update role route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = role_service.update_role(
        db_session, role_id, data, authenticated_user)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@auth_router.put("/roles/{role_id}/")
async def put_update_role_route():
    """Update role Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@auth_router.get(
    "/roles/{role_id}/",
    response_model=RoleSerializerSchema,
    description="Retrives an existing role",
)
async def get_role_route(
    role_id: int,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "auth", "model": "role", "action": "view"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Get role route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = role_service.get_role(role_id, db_session)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@auth_router.get(
    "/permissions/",
    response_model=Page[PermissionSerializerSchema],
    description="Retrie list of permissions. Can apply filters",
)
async def get_list_permission_route(
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "auth", "model": "permission", "action": "view"})
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
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    return permission_serivce.get_permissions(db_session, page, size, search)


@auth_router.post("/send-new-password/", description="Send new password to an user")
async def post_send_new_password_route(
    data: NewPasswordSchema,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "auth", "model": "permissions", "action": "admin"}
        )  # action admin não existe, isso garante que só role Administrador consiga acessar
    ),
    db_session: Session = Depends(get_db_session),
) -> JSONResponse:
    """Sends new password to the user"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    user_service.send_new_password(data, db_session, authenticated_user)

    return JSONResponse(content="", status_code=status.HTTP_200_OK)
