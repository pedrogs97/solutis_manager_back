"""Tests for lending router v2"""

from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from src.lending.controllers.lending import LendingController
from src.main import appAPI

client = TestClient(appAPI)


def test_create_lending_flow_route_success():
    """
    Test the successful creation of a lending flow via the v2 router.
    """
    mock_controller = MagicMock(spec=LendingController)
    mock_controller.create_lending_flow = AsyncMock(
        return_value={"lending": {"id": 1}, "document": {"id": 1}}
    )
    appAPI.dependency_overrides[LendingController] = lambda: mock_controller

    response = client.post("/api/v2/lendings/")

    assert response.status_code == 201
    assert response.json() == {"lending": {"id": 1}, "document": {"id": 1}}
    mock_controller.create_lending_flow.assert_awaited_once()
    appAPI.dependency_overrides = {}


def test_create_lending_flow_route_unauthenticated():
    """
    Test that the lending flow route returns a 401 Unauthorized error
    when the user is not authenticated.
    """

    def _raise_unauthorized():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    appAPI.dependency_overrides[LendingController] = _raise_unauthorized

    response = client.post("/api/v2/lendings/")

    assert response.status_code == 401
    appAPI.dependency_overrides = {}
