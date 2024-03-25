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
from src.term.filters import TermFilter
from src.term.schemas import NewTermSchema, UpdateTermSchema
from src.term.service import TermService

term_router = APIRouter(prefix="/terms", tags=["Term"])

term_service = TermService()


@term_router.post("/")
def post_create_term_route(
    data: NewTermSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "term", "action": "add"})
    ),
):
    """
    Creates a term route.

    Args:
        data (NewTermSchema): The data required to create a term.
        db_session (Session): The SQLAlchemy database session.
        authenticated_user (Union[UserModel, None]): The authenticated user making the request.

    Returns:
        JSONResponse: The response containing the serialized term data if the term was created successfully,
        or a 401 Unauthorized response if the user is not authenticated.
    """
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer = term_service.create_term(data, db_session, authenticated_user)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_201_CREATED,
    )


@term_router.get("/")
def get_list_terms_route(
    term_filters: TermFilter = FilterDepends(TermFilter),
    page: int = Query(1, ge=1, description=PAGE_NUMBER_DESCRIPTION),
    size: int = Query(
        PAGINATION_NUMBER,
        ge=1,
        le=MAX_PAGINATION_NUMBER,
        description=PAGE_SIZE_DESCRIPTION,
    ),
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "term", "action": "view"})
    ),
):
    """List terms and apply filters route

    Retrieves a list of terms and applies filters based on the provided parameters.

    Args:
        search (str, optional): A string used for searching terms. Defaults to "".
        term_filters (str, optional): A string used for filtering terms based on asset. Defaults to None.
        page (int, optional): An integer representing the page number of the results. Defaults to 1.
        size (int, optional): An integer representing the number of results per page. Defaults to PAGINATION_NUMBER.
        db_session (Session, optional): The database session. Defaults to Depends(get_db_session).
        authenticated_user (Union[UserModel, None], optional): The authenticated user. Defaults to Depends(PermissionChecker).

    Returns:
        JSONResponse: JSON response containing the retrieved terms with a status code of 200.
    """
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    terms = term_service.get_terms(db_session, term_filters, page, size)
    db_session.close()
    return terms


@term_router.get("/{term_id}/")
def get_term_route(
    term_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "term", "action": "view"})
    ),
):
    """
    Get term information for a specific term ID.

    Args:
        term_id (int): The ID of the term to retrieve.
        db_session (Session, optional): An instance of the SQLAlchemy Session class for database operations.
            Defaults to Depends(get_db_session).
        authenticated_user (Union[UserModel, None], optional): An instance of the UserModel class or None,
            obtained from the PermissionChecker dependency. Defaults to Depends(PermissionChecker(...)).

    Returns:
        JSONResponse: A JSON response containing the serialized term information and a status code.
    """
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer = term_service.get_term(term_id, db_session)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@term_router.patch("/{term_id}/")
def patch_term_route(
    term_id: int,
    data: UpdateTermSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "lending", "model": "term", "action": "edit"})
    ),
):
    """
    Update term information for a specific term ID.
    """
    if not authenticated_user:
        db_session.close()
        return JSONResponse(content=NOT_ALLOWED, status_code=status.HTTP_403_FORBIDDEN)
    serializer = term_service.update_term(term_id, data, db_session, authenticated_user)
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )
