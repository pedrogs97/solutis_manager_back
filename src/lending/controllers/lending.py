"""Lending controller"""

import os
from typing import Annotated, Any, List, Optional, Tuple, Union

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
        created_file_paths: List[str] = []
        try:
            lending_data = NewLendingSchema(**self.data.model_dump(by_alias=True))
            new_lending = self.lending_service.create_lending(
                lending_data,
                self.db_session,
                self.authenticated_user,
                auto_commit=False,
            )

            if self.attachments:
                for attachment in self.attachments:
                    uploaded_path = await self.attachment_service.upload_attachment(
                        new_lending.id,
                        attachment,
                        auto_commit=False,
                    )
                    if uploaded_path:
                        created_file_paths.append(uploaded_path)

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
            if new_document.path:
                created_file_paths.append(new_document.path)

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
                    auto_commit=False,
                )

            self.db_session.commit()

            return {
                "lending": new_lending.model_dump(by_alias=True),
                "document": new_document.model_dump(by_alias=True),
                "verfication": [
                    (
                        verification
                        if isinstance(verification, dict)
                        else verification.model_dump(by_alias=True)
                    )
                    for verification in new_verification
                ],
            }
        except HTTPException as error:
            self._cleanup_files(created_file_paths)
            fields, reasons = self._extract_error_summary(error.detail)
            logger.warning(
                "Falha no fluxo de criação de comodato. status_code={}, campos={}, motivos={}",
                error.status_code,
                fields,
                reasons,
            )
            raise
        except ValidationError as error:
            self._cleanup_files(created_file_paths)
            fields, reasons = self._extract_error_summary(error.errors())
            logger.warning(
                "Erro de validação no fluxo de criação de comodato. campos={}, motivos={}",
                fields,
                reasons,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error.errors(),
            ) from error
        except Exception as error:
            self._cleanup_files(created_file_paths)
            logger.exception(
                "Erro inesperado no fluxo de criação de comodato. tipo={}, motivo={}",
                type(error).__name__,
                str(error),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ocorreu um erro ao criar o fluxo de comodato.",
            ) from error

    @staticmethod
    def _extract_error_summary(detail: Any) -> Tuple[List[str], List[str]]:
        """Extrai resumo de erros para logs: campos e motivos."""
        fields: List[str] = []
        reasons: List[str] = []

        def _append(field: Optional[str], reason: Optional[str]) -> None:
            if field and field not in fields:
                fields.append(field)
            if reason and reason not in reasons:
                reasons.append(reason)

        if isinstance(detail, dict):
            _append(
                detail.get("field"),
                detail.get("error") or detail.get("message") or str(detail),
            )
            return fields, reasons

        if isinstance(detail, list):
            for item in detail:
                if isinstance(item, dict):
                    loc = item.get("loc")
                    field = None
                    if isinstance(loc, (list, tuple)) and loc:
                        field = str(loc[-1])
                    elif isinstance(loc, str):
                        field = loc
                    else:
                        field = item.get("field")
                    _append(
                        field,
                        item.get("msg") or item.get("error") or item.get("message"),
                    )
                else:
                    _append("general", str(item))
            return fields, reasons

        _append("general", str(detail))
        return fields, reasons

    def _cleanup_files(self, file_paths: List[str]) -> None:
        """Remove arquivos criados durante o fluxo quando a transação falha."""
        for file_path in file_paths:
            if not file_path:
                continue
            if not isinstance(file_path, (str, bytes, os.PathLike)):
                continue

            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.warning(
                        "Arquivo removido por rollback do fluxo de comodato: {}",
                        file_path,
                    )
            except OSError as cleanup_error:
                logger.error(
                    "Falha ao remover arquivo após rollback do fluxo de comodato. path={}, erro={}",
                    file_path,
                    str(cleanup_error),
                )
