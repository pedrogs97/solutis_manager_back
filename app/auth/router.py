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
)
from app.auth.service import create_user, get_users, update_user
from app.backends import (
    get_user,
    get_user_token,
    token_exception,
    logout_user,
    oauth2_bearer,
    PermissionChecker,
    get_db_session,
)


auth_router = APIRouter(prefix="/auth", tags=["Auth"])


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


@auth_router.post("/users/", response_model=UserSerializer)
async def create_user_route(
    data: NewUserSchema,
    authenticated: bool = Depends(
        PermissionChecker({"module": "auth", "model": "user", "method": "add"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """New user route"""
    if not authenticated:
        return JSONResponse(
            content="Not allowed", status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = create_user(data, db_session)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_201_CREATED
    )


@auth_router.patch("/users/{user_id}/", response_model=UserSerializer)
async def update_user_route(
    data: UserUpdateSchema,
    user_id: int,
    authenticated: bool = Depends(
        PermissionChecker({"module": "auth", "model": "user", "method": "edit"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """New user route"""
    if not authenticated:
        return JSONResponse(
            content="Not allowed", status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = update_user(db_session, user_id, data)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_201_CREATED
    )


@auth_router.get("/users/", response_model=Page[UserSerializer])
async def get_list_user_route(
    authenticated: bool = Depends(
        PermissionChecker({"module": "auth", "model": "user", "method": "view"})
    ),
    search: str = "",
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    active: bool = Query(True, description="Active user"),
    staff: Optional[bool] = Query(None, description="Staff user"),
    db_session: Session = Depends(get_db_session),
):
    """List users route"""
    if not authenticated:
        return JSONResponse(
            content="Not allowed", status_code=status.HTTP_401_UNAUTHORIZED
        )

    return get_users(db_session, page, size, search, active, staff)


@auth_router.post("/roles/", response_model=UserSerializer)
async def create_user_route(
    data: NewUserSchema,
    authenticated: bool = Depends(
        PermissionChecker({"module": "auth", "model": "user", "method": "add"})
    ),
    db_session: Session = Depends(get_db_session),
) -> Response:
    """New user route"""
    if not authenticated:
        return JSONResponse(
            content="Not allowed", status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = create_user(data, db_session)
    return JSONResponse(
        serializer.model_dump(by_alias=True), status_code=status.HTTP_201_CREATED
    )
