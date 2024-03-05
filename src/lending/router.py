"""Lending router"""

from typing import Union

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from fastapi_filter import FilterDepends
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.backends import PermissionChecker, get_db_session
from src.config import (
    MAX_PAGINATION_NUMBER,
    NOT_ALLOWED,
    PAGE_NUMBER_DESCRIPTION,
    PAGE_SIZE_DESCRIPTION,
    PAGINATION_NUMBER,
)
from src.lending.filters import LendingFilter, WitnessFilter, WorkloadFilter
from src.lending.schemas import (
    CreateWitnessSchema,
    NewLendingSchema,
    UpdateLendingSchema,
)
from src.lending.service import LendingService

lending_router = APIRouter(prefix="/lendings", tags=["Lending"])

lending_service = LendingService()


@lending_router.post("/")
def post_create_lending_route(
    data: NewLendingSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "lending", "action": "add"})
    ),
):
    """
    Creates a lending route.

    Args:
        data (NewLendingSchema): The data required to create a lending.
        db_session (Session): The SQLAlchemy database session.
        authenticated_user (Union[UserModel, None]): The authenticated user making the request.

    Returns:
        JSONResponse: The response containing the serialized lending data if the lending was created successfully,
        or a 401 Unauthorized response if the user is not authenticated.
    """
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = lending_service.create_lending(data, db_session, authenticated_user)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@lending_router.get("/")
def get_list_lendings_route(
    lending_filters: LendingFilter = FilterDepends(LendingFilter),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "lending", "action": "view"})
    ),
):
    """List lendings and apply filters route

    Retrieves a list of lendings and applies filters based on the provided parameters.

    Args:
        search (str, optional): A string used for searching lendings. Defaults to "".
        lending_filters (str, optional): A string used for filtering lendings based on asset. Defaults to None.
        page (int, optional): An integer representing the page number of the results. Defaults to 1.
        size (int, optional): An integer representing the number of results per page. Defaults to PAGINATION_NUMBER.
        db_session (Session, optional): The database session. Defaults to Depends(get_db_session).
        authenticated_user (Union[UserModel, None], optional): The authenticated user. Defaults to Depends(PermissionChecker).

    Returns:
        JSONResponse: JSON response containing the retrieved lendings with a status code of 200.
    """
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    lendings = lending_service.get_lendings(db_session, lending_filters, page, size)
    db_session.close()
    return lendings


@lending_router.get("/{lending_id}/")
def get_lending_route(
    lending_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "lending", "action": "view"})
    ),
):
    """
    Get lending information for a specific lending ID.

    Args:
        lending_id (int): The ID of the lending to retrieve.
        db_session (Session, optional): An instance of the SQLAlchemy Session class for database operations.
            Defaults to Depends(get_db_session).
        authenticated_user (Union[UserModel, None], optional): An instance of the UserModel class or None,
            obtained from the PermissionChecker dependency. Defaults to Depends(PermissionChecker(...)).

    Returns:
        JSONResponse: A JSON response containing the serialized lending information and a status code.
    """
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = lending_service.get_lending(lending_id, db_session)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@lending_router.patch("/{lending_id}/")
def patch_lending_route(
    lending_id: int,
    data: UpdateLendingSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "lending", "action": "view"})
    ),
):
    """
    Update lending information for a specific lending ID.
    """
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = lending_service.update_lending(
        lending_id, data, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@lending_router.get("-workloads/")
def get_list_workloads_route(
    workload_filters: WorkloadFilter = FilterDepends(WorkloadFilter),
    fields: str = "",
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "workload", "action": "view"})
    ),
):
    """List workloads and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    workloads = lending_service.get_workloads(db_session, workload_filters, fields)
    db_session.close()
    return JSONResponse(content=workloads, status_code=status.HTTP_200_OK)


@lending_router.post("-witness/")
def post_create_witness_route(
    data: CreateWitnessSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "witness", "action": "add"})
    ),
):
    """Create new witness route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    witness = lending_service.create_witness(data, authenticated_user, db_session)
    db_session.close()
    return JSONResponse(content=witness, status_code=status.HTTP_200_OK)


@lending_router.get("-witness/")
def get_list_witness_route(
    witnesses_filters: WitnessFilter = FilterDepends(WitnessFilter),
    fields: str = "",
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "witness", "action": "view"})
    ),
):
    """List witness and apply filters route"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    witness = lending_service.get_witnesses(db_session, witnesses_filters, fields)
    db_session.close()
    return JSONResponse(content=witness, status_code=status.HTTP_200_OK)
