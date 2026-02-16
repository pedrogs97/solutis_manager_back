"""Lending controller"""

from typing import List, Optional, Union

from fastapi import Depends, File, HTTPException, UploadFile, status
from loguru import logger
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
        attachments: Optional[List[UploadFile]] = File(
            description="Anexos do contrato"
        ),
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

    async def create_lending_flow(self) -> LendingDataResponse:
        """
        Orchestrates the creation of a lending, its contract, and attaches files.
        """
        try:
            lending_data = NewLendingSchema(**self.data.model_dump(by_alias=True))
            new_lending = self.lending_service.create_lending(
                lending_data, self.db_session, self.authenticated_user
            )

            if self.attachments:
                for attachment in self.attachments:
                    await self.attachment_service.upload_attachment(
                        new_lending.id, attachment
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
            )

            new_verification = []
            if self.data.verification_answers:
                verification_data = NewVerificationAnswerSchema(
                    lendingId=new_lending.id,
                    **self.data.verification_answers.model_dump(by_alias=True),
                )
                new_verification = self.verification_service.create_answer_verification(
                    verification_data,
                    self.db_session,
                    self.authenticated_user,
                )

            return {
                "lending": new_lending.model_dump(by_alias=True),
                "document": new_document.model_dump(by_alias=True),
                "verfication": [
                    verification.model_dump(by_alias=True)
                    for verification in new_verification
                ],
            }
        except Exception as e:
            logger.error(f"Error creating lending flow: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while creating the lending flow.",
            )
