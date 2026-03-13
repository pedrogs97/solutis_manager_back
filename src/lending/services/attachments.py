"""Lending attachments service"""

import os
from typing import Optional, Union

from fastapi import HTTPException, UploadFile, status
from loguru import logger
from sqlalchemy.orm import Session
from src.config import BASE_DIR, CONTRACT_UPLOAD_DIR, DEBUG
from src.lending.models import AssetModel, DocumentModel, LendingAttachments
from src.lending.services.lending import LendingService
from src.utils import upload_file


class LendingAttachmentService:
    """Lending attachment service"""

    def __init__(self, db_session: Session):
        self.lending_service = LendingService()
        self.db_session = db_session

    def __generate_code(
        self,
        db_session: Session,
        asset: Optional[AssetModel] = None,
        type_code="lending",
    ) -> str:
        """Generate new code for document"""
        new_code = 1
        last_doc: Union[DocumentModel, None] = (
            db_session.query(DocumentModel).order_by(DocumentModel.id.desc()).first()
        )
        if not asset and type_code == "lending":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "assetId", "error": "Ativo não encontrado"},
            )

        if last_doc:
            last_code = last_doc.id
            new_code = last_code + 1
        str_code = str(new_code)

        if type_code == "lending":
            asset_type = getattr(asset, "type", None)
            if asset_type and getattr(asset_type, "acronym", None):
                acronym = asset_type.acronym
            else:
                description = getattr(asset, "description", None) or ""
                if not description:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "field": "assetId",
                            "error": (
                                "Ativo sem sigla de tipo e sem descrição para gerar código."
                            ),
                        },
                    )
                acronym = description[:3]
        else:
            acronym = ""

        return acronym + str_code.zfill(6 - len(str_code))

    async def upload_attachment(
        self, lending_id: int, attachment: UploadFile, auto_commit: bool = True
    ) -> Optional[str]:
        """
        Adds an attachment to a lending record.

        Args:
            lending_id (int): ID of the lending record
            attachment (UploadFile): Attachment data to be added
        """
        file_path = None
        try:
            current_lending = self.lending_service.get_lending_or_404(
                lending_id, self.db_session
            )
            new_attachment = LendingAttachments(lending_id=current_lending.id)
            self.db_session.add(new_attachment)
            self.db_session.flush()
            lending_number = current_lending.number or self.__generate_code(
                self.db_session, current_lending.asset
            )
            new_file_name = f"{lending_number} - {new_attachment.id}.{attachment.filename.split('.')[-1]}"
            UPLOAD_DIR = CONTRACT_UPLOAD_DIR

            if DEBUG:
                UPLOAD_DIR = os.path.join(BASE_DIR, "storage", "lending_attach")
            file_path = await upload_file(
                new_file_name, "lending_attach", attachment.file.read(), UPLOAD_DIR
            )
            new_attachment.file_name = new_file_name
            new_attachment.path = file_path
            self.db_session.add(new_attachment)
            if auto_commit:
                self.db_session.commit()
            else:
                self.db_session.flush()
            logger.info(
                f"Attachment {new_attachment.id} uploaded. Lending {current_lending.id} - {lending_number}"
            )
            return file_path
        except HTTPException:
            if auto_commit:
                self.db_session.rollback()
            raise
        except Exception as exc:
            if auto_commit:
                self.db_session.rollback()
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    logger.warning(
                        "Unable to remove attachment file after failure: {}",
                        file_path,
                    )
            logger.error(f"Error uploading attachment: {str(exc)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"field": "lendingId", "error": "Error uploading attachment."},
            ) from exc
