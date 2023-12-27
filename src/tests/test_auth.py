"""Functional tests for Auth module"""
import time
from datetime import datetime, timedelta

import jwt
import pytest

from src.config import ALGORITHM, BASE_API, PASSWORD_SUPER_USER, SECRET_KEY
from src.tests.base import TestBase


class TestAuthModule(TestBase):
    """
    Auth tests

    This class provides functional tests for the Auth module.
    """

    @pytest.fixture
    def authenticated(self, setup, create_initial_data):
        """Fixture to return token"""
        response = self.client.post(
            f"{BASE_API}/auth/login/",
            data={"username": "agile_admin", "password": PASSWORD_SUPER_USER},
        )
        return response.json()

    def test_auth_login_sucess(self, setup, create_initial_data):
        """Test login success case"""
        expected_key = [
            "id",
            "group",
            "email",
            "full_name",
            "access_token",
            "refresh_token",
            "token_type",
            "expires_in",
            "permissions",
        ]
        response = self.client.post(
            f"{BASE_API}/auth/login/",
            data={"username": "agile_admin", "password": PASSWORD_SUPER_USER},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@email.com"
        assert len(data.keys()) == len(expected_key)
        assert all(a == b for a, b in zip(data.keys(), expected_key))
        user_id = data["id"]
        token = data["access_token"]
        token_type = data["token_type"]
        response = self.client.get(
            f"{BASE_API}/auth/users/{user_id}/",
            headers={"Authorization": f"{token_type} {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id

    def test_auth_login_invalid(self, setup):
        """Test login invalid case"""
        response = self.client.post(
            f"{BASE_API}/auth/login/",
            data={"username": "test_invalid", "password": "test_invalid"},
        )
        assert response.status_code == 401

    def test_auth_refresh_sucess(self, authenticated):
        """Test refresh token success case"""
        expected_key = [
            "id",
            "group",
            "email",
            "full_name",
            "access_token",
            "refresh_token",
            "token_type",
            "expires_in",
            "permissions",
        ]
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        response = self.client.post(
            f"{BASE_API}/auth/refresh-token/",
            json={"refreshToken": authenticated_data["refresh_token"]},
            headers={"Authorization": f"{token_type} {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data.keys()) == len(expected_key)
        assert all(a == b for a, b in zip(data.keys(), expected_key))
        assert data["id"] == authenticated_data["id"]

    def test_auth_refresh_invalid(self, authenticated):
        """Test refresh token invalid case"""
        refresh_encode = {
            "iat": datetime.now().timestamp(),
            "exp": time.mktime((datetime.now() + timedelta(seconds=5)).timetuple()),
            "sub": 0,
            "type": "refresh",
        }

        refresh_token = jwt.encode(refresh_encode, SECRET_KEY, algorithm=ALGORITHM)
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        response = self.client.post(
            f"{BASE_API}/auth/refresh-token/",
            json={"refreshToken": refresh_token},
            headers={"Authorization": f"{token_type} {token}"},
        )
        assert response.status_code == 401

    def test_auth_logout_success(self, authenticated):
        """Test logout success case"""
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        response = self.client.post(
            f"{BASE_API}/auth/logout/",
            headers={"Authorization": f"{token_type} {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "logout"

    def test_auth_logout_invalid(self, setup):
        """Test logout invalid case"""
        response = self.client.post(
            f"{BASE_API}/auth/logout/",
        )
        assert response.status_code == 401

    def test_auth_create_user(self, authenticated):
        """Test logout invalid case"""
        pass
        # authenticated_data = authenticated
        # token = authenticated_data["access_token"]
        # token_type = authenticated_data["token_type"]
        # response = self.client.post(
        #     f"{BASE_API}/auth/users/",
        #     headers={"Authorization": f"{token_type} {token}"},
        #     json={
        #         "username": "test_new_user",
        #         "email": "new_user@email.com",
        #         "groupId": 1,
        #         "employeeId": "test_new_user",
        #     }
        # )
        # assert response.status_code == 401
