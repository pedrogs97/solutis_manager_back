"""Verification router"""

from typing import Union

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.backends import PermissionChecker, get_db_session
from src.config import NOT_ALLOWED
from src.verification.schemas import NewVerificationAnswerSchema, NewVerificationSchema
from src.verification.service import VerificationService

verification_router = APIRouter(prefix="/verifications", tags=["Verification"])

verification_service = VerificationService()


@verification_router.post("/")
def post_create_verifications(
    data: NewVerificationSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "verification", "action": "add"})
    ),
):
    """Creates new verification"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    serializer = verification_service.create_verification(
        data, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=serializer.model_dump(by_alias=True),
        status_code=status.HTTP_200_OK,
    )


@verification_router.get("/{asset_type_id}/")
def get_asset_type_verifications(
    asset_type_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "asset", "model": "verification", "action": "view"}
        )
    ),
):
    """Get asset type verifications"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )

    list_serializer = verification_service.get_asset_verifications(
        asset_type_id, db_session
    )
    db_session.close()
    return JSONResponse(
        content=[
            serializer.model_dump(by_alias=True) for serializer in list_serializer
        ],
        status_code=status.HTTP_200_OK,
    )


@verification_router.post("/answer/")
def post_create_answer_verification(
    data: NewVerificationAnswerSchema,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker({"module": "asset", "model": "verification", "action": "add"})
    ),
):
    """Creates answer for a verification"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    ansers_list = verification_service.create_answer_verification(
        data, db_session, authenticated_user
    )
    db_session.close()
    return JSONResponse(
        content=ansers_list,
        status_code=status.HTTP_200_OK,
    )


@verification_router.get("/answer/{lending_id}/")
def get_answer_verification_by_lending(
    lending_id: int,
    db_session: Session = Depends(get_db_session),
    authenticated_user: Union[UserModel, None] = Depends(
        PermissionChecker(
            {"module": "asset", "model": "verification", "action": "view"}
        )
    ),
):
    """Creates answer for a verification"""
    if not authenticated_user:
        db_session.close()
        return JSONResponse(
            content=NOT_ALLOWED, status_code=status.HTTP_401_UNAUTHORIZED
        )
    ansers_list = verification_service.get_answer_verification_by_lending(
        lending_id, db_session
    )
    db_session.close()
    return JSONResponse(
        content=ansers_list,
        status_code=status.HTTP_200_OK,
    )
