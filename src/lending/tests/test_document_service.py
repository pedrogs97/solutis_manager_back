"""Tests for document service contract helpers."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.document.schemas import NewLendingDocSchema
from src.document.service import DocumentService


def _build_asset(value):
    return SimpleNamespace(
        type=SimpleNamespace(id=1),
        register_number="NB-001",
        serial_number="SN-001",
        description="Notebook",
        accessories="Fonte",
        pattern=None,
        operational_system=None,
        value=value,
        model=None,
        brand=None,
        imei=None,
        operator=None,
        line_number=None,
        observations=None,
    )


def test_get_contract_detail_handles_null_asset_value_without_raising():
    service = DocumentService()
    asset = _build_asset(value=None)

    detail = service._DocumentService__get_contract_detail(
        asset=asset,
        cost_center="100",
        ms_office=False,
    )

    value_row = next(row for row in detail if row["key"] == "Valor R$")
    assert value_row["value"] == service.NOT_PROVIDE


def test_get_contract_detail_handles_invalid_asset_value_without_raising():
    service = DocumentService()
    asset = _build_asset(value="invalid-value")

    detail = service._DocumentService__get_contract_detail(
        asset=asset,
        cost_center="100",
        ms_office=True,
    )

    value_row = next(row for row in detail if row["key"] == "Valor R$")
    assert value_row["value"] == service.NOT_PROVIDE


def test_build_lending_attachments_context_returns_400_for_missing_file():
    service = DocumentService()
    missing_attachment = SimpleNamespace(
        path="/tmp/does-not-exist.pdf",
        file_name="does-not-exist.pdf",
    )

    with pytest.raises(HTTPException) as exception_info:
        service._DocumentService__build_lending_attachments_context(
            [missing_attachment]
        )

    assert exception_info.value.status_code == 400
    assert exception_info.value.detail[0]["field"] == "attachments"


def test_generate_code_returns_400_when_asset_has_no_type_or_description():
    service = DocumentService()
    asset = SimpleNamespace(type=None, description=None)
    last_doc = SimpleNamespace(id=41)

    with pytest.raises(HTTPException) as exception_info:
        service._DocumentService__generate_code(last_doc=last_doc, asset=asset)

    assert exception_info.value.status_code == 400
    assert exception_info.value.detail == {
        "field": "assetId",
        "error": "Ativo sem sigla de tipo e sem descrição para gerar código.",
    }


def test_create_contract_logs_warning_when_http_exception_occurs():
    service = DocumentService()
    db_session = MagicMock()
    authenticated_user = MagicMock()
    payload = NewLendingDocSchema(lendingId=999, legalPerson=False)

    query_doc_type = MagicMock()
    query_doc_type.filter.return_value = query_doc_type
    query_doc_type.first.return_value = None

    query_lending_status = MagicMock()
    query_lending_status.filter.return_value = query_lending_status
    query_lending_status.first.return_value = None

    query_lending = MagicMock()
    query_lending.filter.return_value = query_lending
    query_lending.first.return_value = None

    db_session.query.side_effect = [
        query_doc_type,
        query_lending_status,
        query_lending,
    ]

    with patch("src.document.service.logger.warning") as mock_warning:
        with pytest.raises(HTTPException) as exception_info:
            service.create_contract(
                payload,
                "Contrato de Comodato",
                db_session,
                authenticated_user,
                auto_commit=True,
            )

    assert exception_info.value.status_code == 404
    db_session.rollback.assert_called_once()
    mock_warning.assert_called_once()


def test_get_verification_document_returns_400_for_missing_lending_number():
    service = DocumentService()
    db_session = MagicMock()
    authenticated_user = MagicMock()

    lending = SimpleNamespace(id=1, number=None)

    query_document = MagicMock()
    query_document.filter.return_value = query_document
    query_document.first.return_value = None

    query_verification_answers = MagicMock()
    query_verification_answers.join.return_value = query_verification_answers
    query_verification_answers.filter.return_value = query_verification_answers
    query_verification_answers.all.return_value = []

    db_session.query.side_effect = [
        query_document,
        query_verification_answers,
    ]

    with patch.object(
        service, "_DocumentService__get_lending_or_404", return_value=lending
    ):
        with pytest.raises(HTTPException) as exception_info:
            service.get_verification_document(
                lendind_id=1,
                db_session=db_session,
                authenticated_user=authenticated_user,
            )

    assert exception_info.value.status_code == 400
    assert exception_info.value.detail == {
        "field": "lendingId",
        "error": "Comodato sem número",
    }
    db_session.rollback.assert_called_once()


def test_sign_document_propagates_http_exception_for_invalid_document_type():
    service = DocumentService()
    db_session = MagicMock()

    document = SimpleNamespace(
        id=10,
        doc_type_id=9999,
        doc_type=SimpleNamespace(name="Desconhecido"),
        file_name="doc.pdf",
        path="/tmp/doc.pdf",
    )

    with patch.object(
        service, "_DocumentService__get_document_or_404", return_value=document
    ):
        with pytest.raises(HTTPException) as exception_info:
            service.sign_document(document_id=10, db_session=db_session)

    assert exception_info.value.status_code == 400
    assert exception_info.value.detail == {
        "field": "documentId",
        "error": "Tipo de documento inválido para assinatura",
    }
    db_session.rollback.assert_called_once()
