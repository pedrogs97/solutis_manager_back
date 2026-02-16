"""Tests for lending controller"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
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
