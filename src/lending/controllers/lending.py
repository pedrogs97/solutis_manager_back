"""Lending controller"""

from typing import Annotated, List, Optional, Union

from fastapi import Depends, File, Form, HTTPException, UploadFile, status
from loguru import logger
from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.backends import PermissionChecker, get_db_session
from src.config import NOT_ALLOWED
from src.document.schemas import NewLendingDocSchema
from src.document.service import DocumentService
from src.lending.schemas.v1 import NewLendingSchema
from src.lending.schemas.v2 import NewLendingDataSchema
from src.lending.services.attachments import LendingAttachmentService
from src.lending.services.lending import LendingService
from src.lending.types.responses import LendingDataResponse
from src.verification.service import NewVerificationAnswerSchema, VerificationService


class LendingController:
    """Lending controller"""

    def __init__(
        self,
        data: NewLendingDataSchema,
        attachments: Optional[List[UploadFile]] = None,
        db_session: Session = Depends(get_db_session),
        authenticated_user: Union[UserModel, None] = Depends(
            PermissionChecker(
                {"module": "lending", "model": "lending", "action": "add"}
            )
        ),
    ):
        if not authenticated_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=NOT_ALLOWED,
            )
        self.db_session = db_session
        self.authenticated_user = authenticated_user
        self.lending_service = LendingService()
        self.document_service = DocumentService()
        self.attachment_service = LendingAttachmentService(db_session=db_session)
        self.verification_service = VerificationService()
        self.data = data
        self.attachments = attachments

    @staticmethod
    def from_multipart(
        data: Annotated[str, Form(...)],
        attachments: Annotated[
            List[UploadFile], File(description="Anexos do contrato")
        ] = None,
        db_session: Session = Depends(get_db_session),
        authenticated_user: Union[UserModel, None] = Depends(
            PermissionChecker(
                {"module": "lending", "model": "lending", "action": "add"}
            )
        ),
    ) -> "LendingController":
        """Parses multipart payload and instantiates LendingController."""
        try:
            parsed_data = NewLendingDataSchema.model_validate_json(data)
        except ValidationError as exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exception.errors(),
            ) from exception

        return LendingController(
            data=parsed_data,
            attachments=attachments or [],
            db_session=db_session,
            authenticated_user=authenticated_user,
        )

    async def create_lending_flow(self) -> LendingDataResponse:
        """
        Orchestrates the creation of a lending, its contract, and attaches files.
        """
        try:
            with self.db_session.begin():
                lending_data = NewLendingSchema(**self.data.model_dump(by_alias=True))
                new_lending = self.lending_service.create_lending(
                    lending_data,
                    self.db_session,
                    self.authenticated_user,
                    auto_commit=False,
                )

                if self.attachments:
                    for attachment in self.attachments:
                        await self.attachment_service.upload_attachment(
                            new_lending.id,
                            attachment,
                            auto_commit=False,
                        )

                doc_data = NewLendingDocSchema(
                    lendingId=new_lending.id,
                    legalPerson=self.data.legal_person or False,
                )
                new_document = self.document_service.create_contract(
                    doc_data,
                    "Contrato de Comodato",
                    self.db_session,
                    self.authenticated_user,
                    auto_commit=False,
                )

                new_verification = []
                if self.data.verification_answers:
                    verification_data = NewVerificationAnswerSchema(
                        lendingId=new_lending.id,
                        **self.data.verification_answers.model_dump(by_alias=True),
                    )
                    new_verification = (
                        self.verification_service.create_answer_verification(
                            verification_data,
                            self.db_session,
                            self.authenticated_user,
                            auto_commit=False,
                        )
                    )

            return {
                "lending": new_lending.model_dump(by_alias=True),
                "document": new_document.model_dump(by_alias=True),
                "verfication": [
                    verification.model_dump(by_alias=True)
                    for verification in new_verification
                ],
            }
        except HTTPException as error:
            logger.warning(
                "Lending flow failed with HTTP {}: {}",
                error.status_code,
                error.detail,
            )
            raise
        except ValidationError as error:
            logger.warning(f"Validation error creating lending flow: {error}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error.errors(),
            ) from error
        except Exception as error:
            logger.exception(f"Error creating lending flow: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while creating the lending flow.",
            ) from error
