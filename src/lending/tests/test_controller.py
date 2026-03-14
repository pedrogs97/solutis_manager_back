"""Tests for lending controller"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from fastapi import HTTPException
from fastapi import UploadFile
from pydantic import ValidationError

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
    _, create_kwargs = lending_controller.lending_service.create_lending.call_args
    assert create_kwargs["auto_commit"] is False
    assert lending_controller.attachment_service.upload_attachment.call_count == 2
    for call in lending_controller.attachment_service.upload_attachment.call_args_list:
        assert call.kwargs["auto_commit"] is False
    lending_controller.document_service.create_contract.assert_called_once()
    _, document_kwargs = lending_controller.document_service.create_contract.call_args
    assert document_kwargs["auto_commit"] is False
    mock_db_session.commit.assert_called_once()
    mock_db_session.rollback.assert_not_called()

    assert "lending" in result
    assert "document" in result
    assert "verfication" in result
    assert result["lending"] == {"id": 1}


def test_create_lending_flow_with_verification_answers_dict_response(
    mock_db_session, mock_authenticated_user
):
    """
    Ensure v2 flow handles verification service responses already serialized as dict.
    """
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
        verificationAnswers={
            "typeId": 1,
            "answered": [
                {
                    "verificationId": 1,
                    "answer": "Sim",
                    "observations": "",
                }
            ],
        },
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
    lending_controller.verification_service = MagicMock()

    mock_lending = MagicMock()
    mock_lending.id = 1
    mock_lending.model_dump.return_value = {"id": 1}
    lending_controller.lending_service.create_lending.return_value = mock_lending

    mock_document = MagicMock()
    mock_document.model_dump.return_value = {"id": 10}
    lending_controller.document_service.create_contract.return_value = mock_document

    lending_controller.verification_service.create_answer_verification.return_value = [
        {
            "id": 1,
            "lendingId": 1,
            "answer": "Sim",
        }
    ]

    result = asyncio.run(lending_controller.create_lending_flow())

    assert result["verfication"] == [
        {
            "id": 1,
            "lendingId": 1,
            "answer": "Sim",
        }
    ]
    lending_controller.verification_service.create_answer_verification.assert_called_once()
    _, verification_kwargs = (
        lending_controller.verification_service.create_answer_verification.call_args
    )
    assert verification_kwargs["auto_commit"] is False


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

    with patch("src.lending.controllers.lending.logger.warning") as mock_warning:
        with pytest.raises(HTTPException) as exception_info:
            asyncio.run(lending_controller.create_lending_flow())

    assert exception_info.value.status_code == 400
    assert exception_info.value.detail == {
        "field": "assetId",
        "error": "Ativo já vinculado",
    }
    mock_warning.assert_called_once()
    warning_args = mock_warning.call_args.args
    assert warning_args[0].startswith("Falha no fluxo de criação de comodato.")
    assert 400 in warning_args
    assert ["assetId"] in warning_args
    assert ["Ativo já vinculado"] in warning_args


def test_create_lending_flow_propagates_document_validation_http_exception(
    mock_db_session, mock_authenticated_user
):
    """Ensure contract-generation validation errors return as HTTP 400."""
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

    mock_lending = MagicMock()
    mock_lending.id = 1
    lending_controller.lending_service.create_lending.return_value = mock_lending
    lending_controller.document_service.create_contract.side_effect = HTTPException(
        status_code=400,
        detail=[
            {
                "field": "attachments",
                "error": "Arquivo de anexo não encontrado para geração do contrato.",
            }
        ],
    )

    with patch("src.lending.controllers.lending.logger.warning") as mock_warning:
        with pytest.raises(HTTPException) as exception_info:
            asyncio.run(lending_controller.create_lending_flow())

    assert exception_info.value.status_code == 400
    assert exception_info.value.detail == [
        {
            "field": "attachments",
            "error": "Arquivo de anexo não encontrado para geração do contrato.",
        }
    ]
    mock_warning.assert_called_once()


def test_create_lending_flow_removes_uploaded_files_on_document_failure(
    mock_db_session, mock_authenticated_user
):
    """Ensure uploaded files are removed when flow fails after attachment upload."""
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
    attachments = [UploadFile(filename="test1.jpg", file=MagicMock())]

    lending_controller = LendingController(
        data=lending_data,
        attachments=attachments,
        db_session=mock_db_session,
        authenticated_user=mock_authenticated_user,
    )
    lending_controller.lending_service = MagicMock()
    lending_controller.document_service = MagicMock()
    lending_controller.attachment_service = MagicMock()
    lending_controller.attachment_service.upload_attachment = AsyncMock(
        return_value="/tmp/lending_attach_1.jpg"
    )

    mock_lending = MagicMock()
    mock_lending.id = 1
    lending_controller.lending_service.create_lending.return_value = mock_lending
    lending_controller.document_service.create_contract.side_effect = HTTPException(
        status_code=400,
        detail={"field": "document", "error": "Falha ao gerar contrato"},
    )

    with patch("src.lending.controllers.lending.os.path.exists", return_value=True):
        with patch("src.lending.controllers.lending.os.remove") as mock_remove:
            with pytest.raises(HTTPException):
                asyncio.run(lending_controller.create_lending_flow())

    mock_remove.assert_called_once_with("/tmp/lending_attach_1.jpg")


def test_create_lending_flow_propagates_attachment_http_exception(
    mock_db_session, mock_authenticated_user
):
    """Ensure attachment upload HTTP errors are propagated with original payload."""
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
    attachments = [UploadFile(filename="test1.jpg", file=MagicMock())]

    lending_controller = LendingController(
        data=lending_data,
        attachments=attachments,
        db_session=mock_db_session,
        authenticated_user=mock_authenticated_user,
    )
    lending_controller.lending_service = MagicMock()
    lending_controller.document_service = MagicMock()
    lending_controller.attachment_service = MagicMock()
    lending_controller.attachment_service.upload_attachment = AsyncMock(
        side_effect=HTTPException(
            status_code=400,
            detail={"field": "attachments", "error": "Anexo inválido"},
        )
    )

    mock_lending = MagicMock()
    mock_lending.id = 1
    lending_controller.lending_service.create_lending.return_value = mock_lending

    with patch("src.lending.controllers.lending.logger.warning") as mock_warning:
        with pytest.raises(HTTPException) as exception_info:
            asyncio.run(lending_controller.create_lending_flow())

    assert exception_info.value.status_code == 400
    assert exception_info.value.detail == {
        "field": "attachments",
        "error": "Anexo inválido",
    }
    lending_controller.document_service.create_contract.assert_not_called()
    mock_warning.assert_called_once()


def test_create_lending_flow_returns_500_on_unexpected_document_exception(
    mock_db_session, mock_authenticated_user
):
    """Ensure unexpected document-generation exceptions become generic 500."""
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

    mock_lending = MagicMock()
    mock_lending.id = 1
    lending_controller.lending_service.create_lending.return_value = mock_lending
    lending_controller.document_service.create_contract.side_effect = RuntimeError(
        "template render failed"
    )

    with patch("src.lending.controllers.lending.logger.exception") as mock_exception:
        with pytest.raises(HTTPException) as exception_info:
            asyncio.run(lending_controller.create_lending_flow())

    assert exception_info.value.status_code == 500
    assert exception_info.value.detail == "Ocorreu um erro ao criar o fluxo de comodato."
    mock_exception.assert_called_once()
    exception_args = mock_exception.call_args.args
    assert exception_args[0].startswith("Erro inesperado no fluxo de criação de comodato.")
    assert "RuntimeError" in exception_args
    assert "template render failed" in exception_args
    mock_db_session.rollback.assert_called_once()
    mock_db_session.commit.assert_not_called()


def test_create_lending_flow_propagates_verification_http_exception(
    mock_db_session, mock_authenticated_user
):
    """Ensure verification HTTP errors keep their specific field and status."""
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
        verificationAnswers={
            "typeId": 1,
            "answered": [
                {
                    "verificationId": 1,
                    "answer": "Sim",
                    "observations": "",
                }
            ],
        },
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
    lending_controller.verification_service = MagicMock()

    mock_lending = MagicMock()
    mock_lending.id = 1
    lending_controller.lending_service.create_lending.return_value = mock_lending

    mock_document = MagicMock()
    mock_document.model_dump.return_value = {"id": 10}
    lending_controller.document_service.create_contract.return_value = mock_document

    lending_controller.verification_service.create_answer_verification.side_effect = (
        HTTPException(
            status_code=404,
            detail={
                "field": "verificationTypeId",
                "error": "Tipo do Verificação não encontrado.",
            },
        )
    )

    with patch("src.lending.controllers.lending.logger.warning") as mock_warning:
        with pytest.raises(HTTPException) as exception_info:
            asyncio.run(lending_controller.create_lending_flow())

    assert exception_info.value.status_code == 404
    assert exception_info.value.detail == {
        "field": "verificationTypeId",
        "error": "Tipo do Verificação não encontrado.",
    }
    mock_warning.assert_called_once()


def test_create_lending_flow_removes_uploaded_and_contract_files_on_verification_failure(
    mock_db_session, mock_authenticated_user
):
    """Ensure flow cleanup removes attachment and generated contract files on rollback."""
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
        verificationAnswers={
            "typeId": 1,
            "answered": [
                {
                    "verificationId": 1,
                    "answer": "Sim",
                    "observations": "",
                }
            ],
        },
    )
    attachments = [UploadFile(filename="test1.jpg", file=MagicMock())]

    lending_controller = LendingController(
        data=lending_data,
        attachments=attachments,
        db_session=mock_db_session,
        authenticated_user=mock_authenticated_user,
    )
    lending_controller.lending_service = MagicMock()
    lending_controller.document_service = MagicMock()
    lending_controller.attachment_service = MagicMock()
    lending_controller.attachment_service.upload_attachment = AsyncMock(
        return_value="/tmp/lending_attach_1.jpg"
    )
    lending_controller.verification_service = MagicMock()

    mock_lending = MagicMock()
    mock_lending.id = 1
    lending_controller.lending_service.create_lending.return_value = mock_lending

    mock_document = MagicMock()
    mock_document.path = "/tmp/contract_1.pdf"
    mock_document.model_dump.return_value = {
        "id": 10,
        "path": "/tmp/contract_1.pdf",
    }
    lending_controller.document_service.create_contract.return_value = mock_document
    lending_controller.verification_service.create_answer_verification.side_effect = (
        HTTPException(
            status_code=404,
            detail={"field": "verificationTypeId", "error": "Tipo não encontrado"},
        )
    )

    with patch("src.lending.controllers.lending.os.path.exists", return_value=True):
        with patch("src.lending.controllers.lending.os.remove") as mock_remove:
            with pytest.raises(HTTPException):
                asyncio.run(lending_controller.create_lending_flow())

    mock_remove.assert_has_calls(
        [
            call("/tmp/lending_attach_1.jpg"),
            call("/tmp/contract_1.pdf"),
        ],
        any_order=True,
    )


def test_create_lending_flow_returns_500_on_unexpected_verification_exception(
    mock_db_session, mock_authenticated_user
):
    """Ensure unexpected verification errors become generic 500 for frontend fallback."""
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
        verificationAnswers={
            "typeId": 1,
            "answered": [
                {
                    "verificationId": 1,
                    "answer": "Sim",
                    "observations": "",
                }
            ],
        },
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
    lending_controller.verification_service = MagicMock()

    mock_lending = MagicMock()
    mock_lending.id = 1
    mock_lending.model_dump.return_value = {"id": 1}
    lending_controller.lending_service.create_lending.return_value = mock_lending

    mock_document = MagicMock()
    mock_document.model_dump.return_value = {"id": 10}
    lending_controller.document_service.create_contract.return_value = mock_document

    lending_controller.verification_service.create_answer_verification.side_effect = (
        RuntimeError("database timeout")
    )

    with patch("src.lending.controllers.lending.logger.exception") as mock_exception:
        with pytest.raises(HTTPException) as exception_info:
            asyncio.run(lending_controller.create_lending_flow())

    assert exception_info.value.status_code == 500
    assert exception_info.value.detail == "Ocorreu um erro ao criar o fluxo de comodato."
    mock_exception.assert_called_once()
    exception_args = mock_exception.call_args.args
    assert exception_args[0].startswith("Erro inesperado no fluxo de criação de comodato.")
    assert "RuntimeError" in exception_args
    assert "database timeout" in exception_args


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
    mock_db_session.rollback.assert_called_once()
    mock_db_session.commit.assert_not_called()


def test_create_lending_flow_rolls_back_transaction_on_business_http_exception(
    mock_db_session, mock_authenticated_user
):
    """Ensure DB transaction rolls back when service raises HTTPException."""
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
    attachments = [UploadFile(filename="test1.jpg", file=MagicMock())]

    lending_controller = LendingController(
        data=lending_data,
        attachments=attachments,
        db_session=mock_db_session,
        authenticated_user=mock_authenticated_user,
    )
    lending_controller.lending_service = MagicMock()
    lending_controller.document_service = MagicMock()
    lending_controller.attachment_service = MagicMock()
    lending_controller.attachment_service.upload_attachment = AsyncMock(
        side_effect=HTTPException(
            status_code=400,
            detail={"field": "attachments", "error": "Anexo inválido"},
        )
    )

    mock_lending = MagicMock()
    mock_lending.id = 1
    lending_controller.lending_service.create_lending.return_value = mock_lending

    with pytest.raises(HTTPException):
        asyncio.run(lending_controller.create_lending_flow())

    mock_db_session.rollback.assert_called_once()
    mock_db_session.commit.assert_not_called()


def test_from_multipart_raises_422_for_invalid_schema_data(
    mock_db_session, mock_authenticated_user
):
    """Ensure semantically invalid JSON payload also returns HTTP 422."""
    data = json.dumps(
        {
            "employeeId": "invalid-id",
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

    with pytest.raises(HTTPException) as exception_info:
        LendingController.from_multipart(
            data=data,
            attachments=[],
            db_session=mock_db_session,
            authenticated_user=mock_authenticated_user,
        )

    assert exception_info.value.status_code == 422


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
