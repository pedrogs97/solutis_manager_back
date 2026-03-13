"""Tests for code generation guards in lending-related services."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.lending.services.attachments import LendingAttachmentService
from src.lending.services.lending import LendingService


def _mock_last_doc_query(db_session: MagicMock, last_doc_id: int = 41) -> None:
    query = MagicMock()
    query.order_by.return_value = query
    query.first.return_value = SimpleNamespace(id=last_doc_id)
    db_session.query.return_value = query


def test_lending_service_generate_code_returns_400_without_acronym_or_description():
    service = LendingService()
    db_session = MagicMock()
    _mock_last_doc_query(db_session)
    asset = SimpleNamespace(type=None, description=None)

    with pytest.raises(HTTPException) as exception_info:
        service._LendingService__generate_code(db_session=db_session, asset=asset)

    assert exception_info.value.status_code == 400
    assert exception_info.value.detail == {
        "field": "assetId",
        "error": "Ativo sem sigla de tipo e sem descrição para gerar código.",
    }


def test_attachment_service_generate_code_returns_400_without_acronym_or_description():
    db_session = MagicMock()
    _mock_last_doc_query(db_session)
    service = LendingAttachmentService(db_session=db_session)
    asset = SimpleNamespace(type=None, description=None)

    with pytest.raises(HTTPException) as exception_info:
        service._LendingAttachmentService__generate_code(
            db_session=db_session,
            asset=asset,
        )

    assert exception_info.value.status_code == 400
    assert exception_info.value.detail == {
        "field": "assetId",
        "error": "Ativo sem sigla de tipo e sem descrição para gerar código.",
    }
