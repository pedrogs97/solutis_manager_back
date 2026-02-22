"""Tests for lending PATCH update behavior."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.lending.schemas.v1 import UpdateLendingSchema
from src.lending.services import lending as lending_module
from src.lending.services.lending import LendingService


def test_update_lending_schema_does_not_require_observations():
    """PATCH schema should accept payloads without observations."""
    data = UpdateLendingSchema(manager="Manager")

    assert data.observations is None
    assert "observations" not in data.model_dump(exclude_unset=True)


def test_update_lending_keeps_observations_when_field_is_omitted(monkeypatch):
    """Omitted observations must not overwrite persisted value."""
    lending = SimpleNamespace(id=1, observations="keep this", manager="old")
    db_session = MagicMock()
    authenticated_user = MagicMock()

    service = LendingService()
    service.get_lending_or_404 = MagicMock(return_value=lending)
    service.serialize_lending = MagicMock(return_value={"id": 1})
    monkeypatch.setattr(lending_module, "service_log", MagicMock())

    result = service.update_lending(
        lending_id=1,
        data=UpdateLendingSchema(manager="new manager"),
        db_session=db_session,
        authenticated_user=authenticated_user,
    )

    assert lending.observations == "keep this"
    assert lending.manager == "new manager"
    assert result == {"id": 1}


def test_update_lending_allows_clearing_observations_with_null(monkeypatch):
    """Explicit null should clear observations on PATCH."""
    lending = SimpleNamespace(id=1, observations="to be cleared")
    db_session = MagicMock()
    authenticated_user = MagicMock()

    service = LendingService()
    service.get_lending_or_404 = MagicMock(return_value=lending)
    service.serialize_lending = MagicMock(return_value={"id": 1})
    monkeypatch.setattr(lending_module, "service_log", MagicMock())

    service.update_lending(
        lending_id=1,
        data=UpdateLendingSchema(observations=None),
        db_session=db_session,
        authenticated_user=authenticated_user,
    )

    assert lending.observations is None
