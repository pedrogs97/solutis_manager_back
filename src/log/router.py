"""Log routes"""

from typing import Union

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.backends import PermissionChecker, get_db_session
from src.config import (
    DEFAULT_DATE_TIME_FORMAT,
    MAX_PAGINATION_NUMBER,
    NOT_ALLOWED,
    PAGE_NUMBER_DESCRIPTION,
    PAGE_SIZE_DESCRIPTION,
    PAGINATION_NUMBER,
)
from src.log.models import LogModel
from src.log.schemas import LogSerializerSchema
from src.people.models import EmployeeModel

log_router = APIRouter(prefix="/logs", tags=["Log"])


@log_router.get("/")
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
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    if search != "":
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
        ).order_by(desc(LogModel.id))
    else:
        log_list = db_session.query(LogModel)

    if filter_list:
        log_list = log_list.join(LogModel.user,).filter(
            or_(
                UserModel.is_active == filter_list,
                UserModel.is_staff == filter_list,
            )
        )

    params = Params(page=page, size=size)
    paginated = paginate(
        log_list,
        params=params,
        transformer=lambda log_list: [
            LogSerializerSchema(
                id=log.id,
                identifier=log.identifier,
                module=log.module,
                model=log.model,
                operation=log.operation,
                logged_in=log.logged_in.strftime(DEFAULT_DATE_TIME_FORMAT),
                user={
                    "id": log.user.id,
                    "fullName": (
                        log.user.employee.full_name if log.user.employee else ""
                    ),
                },
            )
            for log in log_list
        ],
    )
    db_session.close()
    return paginated
