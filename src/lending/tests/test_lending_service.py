"""Tests for lending service error handling."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.lending.schemas.v1 import NewLendingSchema
from src.lending.services.lending import LendingService


def _build_payload() -> NewLendingSchema:
    return NewLendingSchema(
        employeeId=1,
        assetId=1,
        workloadId=1,
        costCenterId=1,
        manager="Gestor Teste",
        location="Recife",
        bu="ADS",
        witnessesId=[2, 3],
        principalSigner="principal@example.com",
        employeeSigner="employee@example.com",
    )


def test_create_lending_propagates_http_exception_without_masking():
    service = LendingService()
    db_session = MagicMock()
    authenticated_user = MagicMock()

    business_error = HTTPException(
        status_code=400,
        detail={"field": "assetId", "error": "Ativo já vinculado"},
    )

    service._LendingService__validate_nested = MagicMock(side_effect=business_error)

    with pytest.raises(HTTPException) as exception_info:
        service.create_lending(
            _build_payload(),
            db_session,
            authenticated_user,
            auto_commit=True,
        )

    assert exception_info.value.status_code == 400
    assert exception_info.value.detail == {
        "field": "assetId",
        "error": "Ativo já vinculado",
    }
    db_session.rollback.assert_called_once()


def test_create_lending_returns_400_for_type_error_instead_of_500():
    service = LendingService()
    db_session = MagicMock()
    authenticated_user = MagicMock()

    service._LendingService__validate_nested = MagicMock(
        side_effect=TypeError("invalid nested payload")
    )

    with pytest.raises(HTTPException) as exception_info:
        service.create_lending(
            _build_payload(),
            db_session,
            authenticated_user,
            auto_commit=True,
        )

    assert exception_info.value.status_code == 400
    assert exception_info.value.detail == {
        "field": "general",
        "error": "Dados inválidos para criar contrato de comodato",
    }
    db_session.rollback.assert_called_once()
