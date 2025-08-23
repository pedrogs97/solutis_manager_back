"""Lending attachments service"""

import os

from fastapi import UploadFile
from sqlalchemy.orm import Session

from src.config import BASE_DIR, CONTRACT_UPLOAD_DIR, DEBUG
from src.lending.models import LendingAttachments
from src.lending.services.lending import LendingService
from src.utils import upload_file


class LendingAttachmentService:
    """Lending attachment service"""

    def __init__(self, db_session: Session):
        self.lending_service = LendingService()
        self.db_session = db_session

    async def upload_attachment(self, lending_id: int, attachment: UploadFile):
        """
        Adds an attachment to a lending record.

        Args:
            lending_id (int): ID of the lending record
            attachment (UploadFile): Attachment data to be added
        """
        current_lending = self.lending_service.get_lending(lending_id, self.db_session)
        new_attachment = LendingAttachments(lending=current_lending)
        self.db_session.add(new_attachment)
        self.db_session.commit()
        self.db_session.refresh(new_attachment)
        new_file_name = f"{current_lending.number} - {new_attachment.id}"
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
