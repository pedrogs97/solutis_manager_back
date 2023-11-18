"""Log routes"""
from typing import Union

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.auth.service import UserSerivce
from src.backends import PermissionChecker, get_db_session
from src.config import (
    MAX_PAGINATION_NUMBER,
    NOT_ALLOWED,
    PAGE_NUMBER_DESCRIPTION,
    PAGE_SIZE_DESCRIPTION,
    PAGINATION_NUMBER,
)
from src.log.models import LogModel
from src.log.schemas import LogSerializerSchema
from src.people.models import EmployeeModel

people_router = APIRouter(prefix="/logs", tags=["Log"])


@people_router.get("/")
def get_list_logs_route(
    search: str = "",
    filter_list: str = None,
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "logs", "model": "log", "action": "view"})
    ),
):
    """List logs and apply filters route"""
    if not authenticated_user:
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    log_list = (
        db_session.query(LogModel)
        .join(UserModel)
        .join(EmployeeModel)
        .filter(
            or_(
                LogModel.operation.ilike(f"%{search}%"),
                EmployeeModel.full_name.ilike(f"%{search}%"),
                UserModel.username.ilike(f"%{search}%"),
                UserModel.email.ilike(f"%{search}%"),
                LogModel.model.ilike(f"%{search}"),
                LogModel.module.ilike(f"%{search}"),
            )
        )
    )

    if filter_list:
        log_list = log_list.join(LogModel.user,).filter(
            or_(
                UserModel.is_active == filter_list,
                UserModel.is_staff == filter_list,
            )
        )

    user_service = UserSerivce()

    params = Params(page=page, size=size)
    paginated = paginate(
        log_list.all(),
        params=params,
        transformer=lambda log_list: [
            LogSerializerSchema(
                **log.__dict__, user=user_service.serialize_user(**log.user)
            )
            for log in log_list
        ],
    )
    db_session.close()
    return paginated
