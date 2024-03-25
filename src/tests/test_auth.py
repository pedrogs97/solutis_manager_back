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
        expected_keys = [
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
        assert len(data.keys()) == len(expected_keys)
        assert all(a == b for a, b in zip(data.keys(), expected_keys))
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
        expected_keys = [
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
        assert len(data.keys()) == len(expected_keys)
        assert all(a == b for a, b in zip(data.keys(), expected_keys))
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
        assert response.status_code == 403

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

    def test_auth_create_user_success(self, authenticated):
        """Test create user API success case"""
        expected_keys = [
            "id",
            "group",
            "fullName",
            "username",
            "email",
            "isStaff",
            "isActive",
            "lastLoginIn",
            "employeeId",
            "department",
            "manager",
        ]
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        payload = {
            "username": "test_new_user",
            "email": "new_user@email.com",
            "groupId": 1,
            "employeeId": 1,
            "department": "ADS",
            "manager": "João da Silva",
        }
        response = self.client.post(
            f"{BASE_API}/auth/users/",
            headers={"Authorization": f"{token_type} {token}"},
            json=payload,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data.keys()) == len(expected_keys)
        assert all(a == b for a, b in zip(data.keys(), expected_keys))
        assert data["username"] == payload["username"]
        assert data["email"] == payload["email"]
        assert data["group"]["id"] == payload["groupId"]
        assert data["employeeId"] == payload["employeeId"]

    def test_auth_create_user_invalid(self, authenticated):
        """Test create user API invalid case"""
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        payload = {
            "username": "test_new_user",
            "email": "new_user@email.com",
            "groupId": 0,
            "employeeId": 0,
            "department": "ADS",
            "manager": "João da Silva",
        }
        response = self.client.post(
            f"{BASE_API}/auth/users/",
            headers={"Authorization": f"{token_type} {token}"},
            json=payload,
        )
        assert response.status_code == 400
        data = response.json()
        assert isinstance(data, list)

    def test_auth_get_users(self, authenticated):
        """Teste get users API case"""
        expected_keys = ["items", "total", "page", "size", "pages"]
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        response = self.client.get(
            f"{BASE_API}/auth/users/",
            headers={"Authorization": f"{token_type} {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data.keys()) == len(expected_keys)
        assert isinstance(data["items"], list)
        assert all(a == b for a, b in zip(data.keys(), expected_keys))

    def test_auth_update_user_success(self, authenticated):
        """Teste update user API success case"""
        expected_keys = [
            "id",
            "group",
            "fullName",
            "username",
            "email",
            "isStaff",
            "isActive",
            "lastLoginIn",
            "employeeId",
            "department",
            "manager",
        ]
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        payload = {"email": "email.update@email.com"}
        response = self.client.patch(
            f"{BASE_API}/auth/users/{1}/",
            headers={"Authorization": f"{token_type} {token}"},
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data.keys()) == len(expected_keys)
        assert all(a == b for a, b in zip(data.keys(), expected_keys))
        assert data["email"] == payload["email"]

    def test_auth_update_user_invalid(self, authenticated):
        """Teste update user API invalid case"""
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        payload = {"groupId": 999}
        response = self.client.patch(
            f"{BASE_API}/auth/users/{1}/",
            headers={"Authorization": f"{token_type} {token}"},
            json=payload,
        )

        assert response.status_code == 400
        data = response.json()
        assert isinstance(data, list)

    def test_auth_get_user_id_success(self, authenticated):
        """Teste get an user API success case"""
        expected_keys = [
            "id",
            "group",
            "fullName",
            "username",
            "email",
            "isStaff",
            "isActive",
            "lastLoginIn",
            "employeeId",
            "department",
            "manager",
        ]
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        response = self.client.get(
            f"{BASE_API}/auth/users/{1}/",
            headers={"Authorization": f"{token_type} {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data.keys()) == len(expected_keys)
        assert all(a == b for a, b in zip(data.keys(), expected_keys))

    def test_auth_get_user_id_invalid(self, authenticated):
        """Teste get an user API invalid case"""
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        response = self.client.get(
            f"{BASE_API}/auth/users/{9999}/",
            headers={"Authorization": f"{token_type} {token}"},
        )

        assert response.status_code == 404

    def test_auth_update_password_success(self, authenticated):
        """Test update password user API success case"""
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        payload = {
            "currentPassword": PASSWORD_SUPER_USER,
            "password": "nova_senha@123",
        }
        response = self.client.post(
            f"{BASE_API}/auth/users/change_password/",
            headers={"Authorization": f"{token_type} {token}"},
            json=payload,
        )

        assert response.status_code == 200

    def test_auth_create_group_success(self, authenticated):
        """Test create group API success case"""
        expected_keys = [
            "id",
            "name",
            "permissions",
        ]
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        payload = {
            "name": "Novo Grupo Teste",
            "permissions": [1, 2, 3, 4],
        }
        response = self.client.post(
            f"{BASE_API}/auth/groups/",
            headers={"Authorization": f"{token_type} {token}"},
            json=payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert len(data.keys()) == len(expected_keys)
        assert all(a == b for a, b in zip(data.keys(), expected_keys))
        assert len(data["permissions"]) == len(payload["permissions"])
        assert all(
            a == b
            for a, b in zip(
                [perm["id"] for perm in data["permissions"]], payload["permissions"]
            )
        )

    def test_auth_create_group_invalid(self, authenticated):
        """Test create group API invalid case"""
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        payload = {
            "name": "Novo Grupo Teste",
            "permissions": [999, 0, 66666, 22222],
        }
        response = self.client.post(
            f"{BASE_API}/auth/groups/",
            headers={"Authorization": f"{token_type} {token}"},
            json=payload,
        )

        assert response.status_code == 400
        data = response.json()
        assert isinstance(data, list)

    def test_auth_get_groups(self, authenticated):
        """Test get groups API case"""
        expected_keys = ["items", "total", "page", "size", "pages"]
        authenticated_data = authenticated
        token = authenticated_data["access_token"]
        token_type = authenticated_data["token_type"]
        response = self.client.get(
            f"{BASE_API}/auth/groups/",
            headers={"Authorization": f"{token_type} {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data.keys()) == len(expected_keys)
        assert isinstance(data["items"], list)
        assert all(a == b for a, b in zip(data.keys(), expected_keys))

    def test_auth_upadate_groups_success(self, authenticated):
        """Test upadate groups API success case"""
        # authenticated_data = authenticated
        # token = authenticated_data["access_token"]
        # token_type = authenticated_data["token_type"]
        # response = self.client.get(l
        #     f"{BASE_API}/auth/groups/",
        #     headers={"Authorization": f"{token_type} {token}"},
        # )

        # assert response.status_code == 200
        # data = response.json()
        # assert len(data.keys()) == len(expected_keys)
        # assert isinstance(data["items"], list)
        # assert all(a == b for a, b in zip(data.keys(), expected_keys))
