"""Lending attachments service"""

import os
from typing import Optional, Union

from fastapi import HTTPException, UploadFile, status
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
            acronym = asset.type.acronym if asset.type else asset.description[:3]
        else:
            acronym = ""

        return acronym + str_code.zfill(6 - len(str_code))

    async def upload_attachment(self, lending_id: int, attachment: UploadFile):
        """
        Adds an attachment to a lending record.

        Args:
            lending_id (int): ID of the lending record
            attachment (UploadFile): Attachment data to be added
        """
        current_lending = self.lending_service.get_lending_or_404(
            lending_id, self.db_session
        )
        new_attachment = LendingAttachments(lending_id=current_lending.id)
        self.db_session.add(new_attachment)
        self.db_session.commit()
        self.db_session.refresh(new_attachment)
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
        self.db_session.commit()
