"""Auth router"""

from typing import Annotated, Union

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm as LoginSchema
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from sqlalchemy.orm import Session

from src.auth.filters import GroupFilter, PermissionFilter, UserFilter
from src.auth.models import UserModel
from src.auth.schemas import (
    GroupSerializerSchema,
    NewGroupSchema,
    NewPasswordSchema,
    NewUserSchema,
    PermissionSerializerSchema,
    RefreshTokenSchema,
    UserChangePasswordSchema,
    UserSerializerSchema,
    UserUpdateSchema,
)
from src.auth.service import GroupService, PermissionService, UserSerivce
from src.backends import (
    PermissionChecker,
    get_db_session,
    get_user,
    get_user_from_refresh,
    get_user_token,
    logout_user,
    oauth2_bearer,
    refresh_token_has_expired,
    token_exception,
)
from src.config import (
    MAX_PAGINATION_NUMBER,
    NOT_ALLOWED,
    PAGE_NUMBER_DESCRIPTION,
    PAGE_SIZE_DESCRIPTION,
    PAGINATION_NUMBER,
)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

user_service = UserSerivce()

group_service = GroupService()

permission_serivce = PermissionService()


@auth_router.post("/login/")
def login_route(
    data: LoginSchema = Depends(),
    db_session: Session = Depends(get_db_session),
):
    """Login user route"""
    user = get_user(data.username, data.password, db_session)
    if not user:
        raise token_exception()
    token = get_user_token(user, db_session)
    db_session.close()
    return JSONResponse(content=token, status_code=status.HTTP_200_OK)


@auth_router.post("/refresh-token/")
def refresh_token_route(
    data: RefreshTokenSchema,
    db_session: Session = Depends(get_db_session),
):
    """Refresh token route"""
    if refresh_token_has_expired(data.refresh_token):
        return JSONResponse(
            content={"refreshToken": "Token inválido"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user = get_user_from_refresh(data.refresh_token, db_session)

    if not user:
        return JSONResponse(
            content="Usuário não encontrado", status_code=status.HTTP_401_UNAUTHORIZED
        )

    token = get_user_token(user, db_session)
    db_session.close()
    return JSONResponse(content=token, status_code=status.HTTP_200_OK)


@auth_router.post("/logout/")
def logout_route(
    token: Annotated[str, Depends(oauth2_bearer)],
    db_session: Session = Depends(get_db_session),
):
    """Logout user route"""
    logout_user(token, db_session)
    db_session.close()
    return JSONResponse(content={"message": "logout"}, status_code=status.HTTP_200_OK)


@auth_router.post(
    "/users/", response_model=UserSerializerSchema, description="Creates new user"
)
def post_create_user_route(
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
    db_session.close()
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_201_CREATED
    )


@auth_router.get(
    "/users/",
    description="Retrie list of users. Can apply filters",
)
def get_list_user_route(
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "auth", "model": "user", "action": "view"})
    ),
    user_filters: UserFilter = FilterDepends(UserFilter),
    employee_empty: bool = Query(False, description="Filter for empty employee"),
    employee_not_empty: bool = Query(
        False, description="Filter for not empty employee"
    ),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
):
    """List users route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    users = user_service.get_users(
        db_session, user_filters, employee_empty, employee_not_empty, page, size
    )
    db_session.close()
    return users


@auth_router.patch(
    "/users/{user_id}/",
    response_model=UserSerializerSchema,
    description="Updates an existing user",
)
def update_user_route(
    data: UserUpdateSchema,
    user_id: int,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "auth", "model": "user", "action": "edit"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Update user route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = user_service.update_user(db_session, user_id, data, authenticated_user)
    db_session.close()
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@auth_router.post(
    "/users/change_password/",
    description="Updates a user's password",
)
def update_user_password_route(
    data: UserChangePasswordSchema,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "auth", "model": "user", "action": "edit"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Update user's password route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    user_service.update_password(data, db_session, authenticated_user)
    db_session.close()
    return JSONResponse("", status_code=status.HTTP_200_OK)


@auth_router.put("/users/{user_id}/")
def put_update_user_route():
    """Update user Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@auth_router.get(
    "/users/{user_id}/",
    response_model=UserSerializerSchema,
    description="Retrives an existing user",
)
def get_user_route(
    user_id: int,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "auth", "model": "user", "action": "view"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Get user route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = user_service.get_user(user_id, db_session)
    db_session.close()
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@auth_router.post(
    "/groups/", response_model=GroupSerializerSchema, description="Creates a new group"
)
def post_create_group_route(
    data: NewGroupSchema,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "auth", "model": "group", "action": "add"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """New group route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = group_service.create_group(data, db_session, authenticated_user)
    db_session.close()
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_201_CREATED
    )


@auth_router.get(
    "/groups/",
    description="Retrie list of groups. Can apply filters",
)
def get_list_group_route(
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "auth", "model": "group", "action": "view"})
    ),
    group_filter: GroupFilter = FilterDepends(GroupFilter),
    fields: str = "",
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
):
    """List groups route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    groups = group_service.get_groups(db_session, group_filter, page, size, fields)
    db_session.close()
    return groups


@auth_router.patch(
    "/groups/{group_id}/",
    response_model=GroupSerializerSchema,
    description="Updates an existing group",
)
def update_group_route(
    data: NewGroupSchema,
    group_id: int,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "auth", "model": "group", "action": "edit"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Update group route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = group_service.update_group(
        db_session, group_id, data, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@auth_router.put("/groups/{group_id}/")
def put_update_group_route():
    """Update group Not Implemented"""
    return JSONResponse(
        content="Não implementado", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@auth_router.get(
    "/groups/{group_id}/",
    response_model=GroupSerializerSchema,
    description="Retrives an existing group",
)
def get_group_route(
    group_id: int,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "auth", "model": "group", "action": "view"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """Get group route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = group_service.get_group(group_id, db_session)
    db_session.close()
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_200_OK
    )


@auth_router.get(
    "/permissions/",
    response_model=Page[PermissionSerializerSchema],
    description="Retrie list of permissions. Can apply filters",
)
def get_list_permission_route(
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "auth", "model": "permission", "action": "view"})
    ),
    permission_filter: PermissionFilter = FilterDepends(PermissionFilter),
    db_session: Session = Depends(get_db_session),
):
    """List permissions route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    permissions = permission_serivce.get_permissions(db_session, permission_filter)
    db_session.close()
    return JSONResponse(content=permissions, status_code=status.HTTP_200_OK)


@auth_router.post("/send-new-password/", description="Send new password to an user")
def post_send_new_password_route(
    data: NewPasswordSchema,
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "auth", "model": "permissions", "action": "admin"}
        )  # action admin não existe, isso garante que só group Administrador consiga acessar
    ),
    db_session: Session = Depends(get_db_session),
) -> JSONResponse:
    """Sends new password to the user"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    user_service.send_new_password(data, db_session, authenticated_user)

    db_session.close()
    return JSONResponse(content="", status_code=status.HTTP_200_OK)
