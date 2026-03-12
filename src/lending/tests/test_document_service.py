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


def test_generate_code_uses_safe_default_when_asset_has_no_type_or_description():
    service = DocumentService()
    asset = SimpleNamespace(type=None, description=None)
    last_doc = SimpleNamespace(id=41)

    code = service._DocumentService__generate_code(last_doc=last_doc, asset=asset)

    assert code == "DOC0042"


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
