"""Tests for lending controller"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi import UploadFile

from src.lending.controllers.lending import LendingController
from src.lending.enums import LendingBUEnum
from src.lending.schemas.v1 import NewLendingSchema
from src.lending.schemas.v2 import NewLendingDataSchema


@pytest.fixture
def mock_db_session():
    """Fixture for a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_authenticated_user():
    """Fixture for a mock authenticated user."""
    user = MagicMock()
    user.is_authenticated = True
    return user


def test_create_lending_flow_successful(mock_db_session, mock_authenticated_user):
    """
    Test the successful creation of a lending flow, including lending, attachments, and contract.
    """
    # Mock data
    lending_data = NewLendingDataSchema(
        employeeId=1,
        assetId=1,
        workloadId=1,
        costCenterId=1,
        manager="Test Manager",
        witnessesId=[2, 3],
        location="Test Location",
        bu=LendingBUEnum.ADS,
        principalSigner="principal@example.com",
        employeeSigner="employee@example.com",
        businessExecutive="Executive",
    )
    attachments = [
        UploadFile(filename="test1.jpg", file=MagicMock()),
        UploadFile(filename="test2.png", file=MagicMock()),
    ]

    lending_controller = LendingController(
        data=lending_data,
        attachments=attachments,
        db_session=mock_db_session,
        authenticated_user=mock_authenticated_user,
    )
    lending_controller.lending_service = MagicMock()
    lending_controller.document_service = MagicMock()
    lending_controller.attachment_service = MagicMock()
    lending_controller.attachment_service.upload_attachment = AsyncMock()

    # Mock service responses
    mock_lending = MagicMock()
    mock_lending.id = 1
    mock_lending.model_dump.return_value = {"id": 1}
    lending_controller.lending_service.create_lending.return_value = mock_lending
    mock_document = MagicMock()
    mock_document.model_dump.return_value = {"id": 10}
    lending_controller.document_service.create_contract.return_value = mock_document

    # Run the flow
    result = asyncio.run(lending_controller.create_lending_flow())

    # Assertions
    lending_controller.lending_service.create_lending.assert_called_once()
    create_args, _ = lending_controller.lending_service.create_lending.call_args
    assert isinstance(create_args[0], NewLendingSchema)
    assert create_args[1] == lending_controller.db_session
    assert create_args[2] == lending_controller.authenticated_user
    assert lending_controller.attachment_service.upload_attachment.call_count == 2
    lending_controller.document_service.create_contract.assert_called_once()

    assert "lending" in result
    assert "document" in result
    assert "verfication" in result
    assert result["lending"] == {"id": 1}


def test_create_lending_flow_propagates_http_exception(
    mock_db_session, mock_authenticated_user
):
    """Ensure business HTTP errors are not masked as generic 500."""
    lending_data = NewLendingDataSchema(
        employeeId=1,
        assetId=1,
        workloadId=1,
        costCenterId=1,
        manager="Test Manager",
        witnessesId=[2, 3],
        location="Test Location",
        bu=LendingBUEnum.ADS,
        principalSigner="principal@example.com",
        employeeSigner="employee@example.com",
        businessExecutive="Executive",
    )

    lending_controller = LendingController(
        data=lending_data,
        attachments=[],
        db_session=mock_db_session,
        authenticated_user=mock_authenticated_user,
    )
    lending_controller.lending_service = MagicMock()
    lending_controller.document_service = MagicMock()
    lending_controller.attachment_service = MagicMock()
    lending_controller.attachment_service.upload_attachment = AsyncMock()

    lending_controller.lending_service.create_lending.side_effect = HTTPException(
        status_code=400, detail={"field": "assetId", "error": "Ativo já vinculado"}
    )

    with pytest.raises(HTTPException) as exception_info:
        asyncio.run(lending_controller.create_lending_flow())

    assert exception_info.value.status_code == 400
    assert exception_info.value.detail == {
        "field": "assetId",
        "error": "Ativo já vinculado",
    }


def test_create_lending_flow_returns_422_on_validation_error(
    mock_db_session, mock_authenticated_user
):
    """Ensure validation errors are returned as 422, not generic 500."""
    lending_data = NewLendingDataSchema(
        employeeId=1,
        assetId=1,
        workloadId=1,
        costCenterId=1,
        manager="Test Manager",
        witnessesId=[2, 3],
        location="Test Location",
        bu=LendingBUEnum.ADS,
        principalSigner="principal@example.com",
        employeeSigner="employee@example.com",
        businessExecutive="Executive",
    )

    lending_controller = LendingController(
        data=lending_data,
        attachments=[],
        db_session=mock_db_session,
        authenticated_user=mock_authenticated_user,
    )
    lending_controller.data = MagicMock()
    lending_controller.data.model_dump.return_value = {}
    lending_controller.lending_service = MagicMock()
    lending_controller.document_service = MagicMock()
    lending_controller.attachment_service = MagicMock()
    lending_controller.attachment_service.upload_attachment = AsyncMock()

    with pytest.raises(HTTPException) as exception_info:
        asyncio.run(lending_controller.create_lending_flow())

    assert exception_info.value.status_code == 422
    lending_controller.lending_service.create_lending.assert_not_called()


def test_from_multipart_parses_json_and_builds_controller(
    mock_db_session, mock_authenticated_user
):
    """Ensure multipart `data` JSON is parsed into NewLendingDataSchema."""
    data = json.dumps(
        {
            "employeeId": 1,
            "assetId": 1,
            "workloadId": 1,
            "costCenterId": 1,
            "manager": "Test Manager",
            "witnessesId": [2, 3],
            "location": "Test Location",
            "bu": "ADS",
            "principalSigner": "principal@example.com",
            "employeeSigner": "employee@example.com",
            "businessExecutive": "Executive",
        }
    )

    controller = LendingController.from_multipart(
        data=data,
        attachments=[],
        db_session=mock_db_session,
        authenticated_user=mock_authenticated_user,
    )

    assert isinstance(controller, LendingController)
    assert isinstance(controller.data, NewLendingDataSchema)
    assert controller.data.employee_id == 1
    assert controller.attachments == []


def test_from_multipart_raises_422_for_invalid_json(
    mock_db_session, mock_authenticated_user
):
    """Ensure malformed JSON in multipart `data` returns HTTP 422."""
    with pytest.raises(HTTPException) as exception_info:
        LendingController.from_multipart(
            data="{invalid",
            attachments=[],
            db_session=mock_db_session,
            authenticated_user=mock_authenticated_user,
        )

    assert exception_info.value.status_code == 422
