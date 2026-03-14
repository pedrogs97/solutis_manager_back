"""Integration-style persistence tests for lending flow transaction behavior."""

import asyncio
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.asset.models import AssetModel, AssetStatusModel, AssetTypeModel
from src.database import Base
from src.datasync.models import (
    CostCenterTOTVSModel,
    EmployeeGenderTOTVSModel,
    EmployeeMaritalStatusTOTVSModel,
    EmployeeNationalityTOTVSModel,
    EmployeeRoleTOTVSModel,
)
from src.lending.controllers.lending import LendingController
from src.lending.enums import LendingBUEnum
from src.lending.models import LendingModel, LendingStatusModel
from src.lending.schemas.v2 import NewLendingDataSchema
from src.maintenance import models as _maintenance_models  # noqa: F401
from src.people.models import EmployeeModel
from src.inventory import models as _inventory_models  # noqa: F401
from src.term import models as _term_models  # noqa: F401


@pytest.fixture
def db_session() -> Session:
    """Creates an isolated in-memory database session for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _seed_dependencies(session: Session) -> dict:
    """Seed minimum records required by FK constraints in lending table."""
    role = EmployeeRoleTOTVSModel(code="DEV", name="Developer")
    nationality = EmployeeNationalityTOTVSModel(code="BRA", description="Brasileira")
    marital_status = EmployeeMaritalStatusTOTVSModel(code="S", description="Solteiro")
    gender = EmployeeGenderTOTVSModel(code="M", description="Masculino")

    employee = EmployeeModel(
        role=role,
        nationality=nationality,
        marital_status=marital_status,
        gender=gender,
        code="EMP001",
        full_name="Colaborador Teste",
        taxpayer_identification="12345678901",
        national_identification="123456789012345",
        address="Rua Teste",
        cell_phone="71999999999",
        email="colaborador.teste@email.com",
        birthday=date(1990, 1, 1),
    )

    asset_type = AssetTypeModel(code="NOTE", name="Notebook", acronym="NOT")
    asset_status = AssetStatusModel(id=1, name="Disponível")
    asset = AssetModel(
        type=asset_type,
        status=asset_status,
        description="Notebook Dell",
        register_number="REG-001",
    )

    cost_center = CostCenterTOTVSModel(
        code="CC001", name="Centro Teste", classification="TI"
    )
    lending_status = LendingStatusModel(name="Arquivo pendente")

    session.add_all(
        [
            role,
            nationality,
            marital_status,
            gender,
            employee,
            asset_type,
            asset_status,
            asset,
            cost_center,
            lending_status,
        ]
    )
    session.flush()
    ids = {
        "employee_id": employee.id,
        "asset_id": asset.id,
        "cost_center_id": cost_center.id,
        "lending_status_id": lending_status.id,
    }
    session.commit()
    return ids


def _build_data(payload: dict) -> NewLendingDataSchema:
    return NewLendingDataSchema(
        employeeId=payload["employee_id"],
        assetId=payload["asset_id"],
        costCenterId=payload["cost_center_id"],
        manager="Gestor Teste",
        location="Salvador",
        bu=LendingBUEnum.ADS,
        principalSigner="gestor@email.com",
        employeeSigner="colaborador@email.com",
        businessExecutive="Executivo Teste",
    )


def _mock_create_lending(session: Session, payload: dict):
    """Returns a mock function that persists LendingModel without committing."""

    def _create_lending(*args, **kwargs):
        new_lending = LendingModel(
            employee_id=payload["employee_id"],
            asset_id=payload["asset_id"],
            cost_center_id=payload["cost_center_id"],
            status_id=payload["lending_status_id"],
            manager="Gestor Teste",
            location="Salvador",
            bu=LendingBUEnum.ADS,
            principal_email_signer="gestor@email.com",
            signer_email="colaborador@email.com",
        )
        session.add(new_lending)
        session.flush()
        return SimpleNamespace(id=new_lending.id, model_dump=lambda **_: {"id": new_lending.id})

    return _create_lending


def test_create_lending_flow_persists_lending_row_on_success(db_session: Session):
    payload = _seed_dependencies(db_session)
    controller = LendingController(
        data=_build_data(payload),
        attachments=[],
        db_session=db_session,
        authenticated_user=MagicMock(),
    )
    controller.lending_service = MagicMock()
    controller.lending_service.create_lending.side_effect = _mock_create_lending(
        db_session, payload
    )
    controller.attachment_service = MagicMock()
    controller.attachment_service.upload_attachment = AsyncMock(return_value=None)
    controller.document_service = MagicMock()
    controller.document_service.create_contract.return_value = SimpleNamespace(
        path=None, model_dump=lambda **_: {"id": 99}
    )
    controller.verification_service = MagicMock()

    asyncio.run(controller.create_lending_flow())

    assert db_session.query(LendingModel).count() == 1


def test_create_lending_flow_rolls_back_persisted_lending_row_on_late_failure(
    db_session: Session,
):
    payload = _seed_dependencies(db_session)
    controller = LendingController(
        data=_build_data(payload),
        attachments=[],
        db_session=db_session,
        authenticated_user=MagicMock(),
    )
    controller.lending_service = MagicMock()
    controller.lending_service.create_lending.side_effect = _mock_create_lending(
        db_session, payload
    )
    controller.attachment_service = MagicMock()
    controller.attachment_service.upload_attachment = AsyncMock(return_value=None)
    controller.document_service = MagicMock()
    controller.document_service.create_contract.side_effect = HTTPException(
        status_code=400, detail={"field": "document", "error": "Falha no contrato"}
    )
    controller.verification_service = MagicMock()

    with pytest.raises(HTTPException):
        asyncio.run(controller.create_lending_flow())

    assert db_session.query(LendingModel).count() == 0
