"""Functional tests for Auth module"""
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.models import GroupModel, PermissionModel, UserModel
from src.auth.service import UserSerivce
from src.backends import get_db_session
from src.config import (
    BASE_API,
    PASSWORD_SUPER_USER,
    PERMISSIONS,
    get_database_server_url,
    get_database_url,
)
from src.database import Base
from src.main import app

load_dotenv()


class TestAuthModule:
    """
    Auth tests

    This class provides functional tests for the Auth module.
    """

    engine_server = None
    testing_session_local = None
    client = None
    engine = None

    @pytest.fixture
    def setup(self):
        """
        Initializes TestAuthModule class and creates a test database.

        Inputs:
        None

        Outputs:
        None
        """
        self.engine_server = create_engine(get_database_server_url())
        connection = self.engine_server.connect()
        try:
            connection.rollback()
            connection.execute(text("CREATE DATABASE db_test"))
            print("Created database")
        except ProgrammingError as prog_err:
            print(prog_err)
            connection.rollback()
        except OperationalError as op_err:
            print(op_err)
            connection.rollback()
        connection.close()

        self.engine = create_engine(get_database_url(test=True), poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.testing_session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        app.dependency_overrides[get_db_session] = self.__override_get_db

        self.client = TestClient(app)
        yield
        connection = self.engine_server.connect()
        connection.execute(text("DROP DATABASE db_test"))
        connection.close()
        print("Dropped database")

    def __override_get_db(self):
        """Get test database"""
        try:
            db = self.testing_session_local()
            yield db
        finally:
            db.close()

    @pytest.fixture
    def create_initial_data(self):
        """Creates super user"""
        db_session = self.testing_session_local()
        group_admin = GroupModel(name="Administrador")
        db_session.add(group_admin)
        db_session.commit()
        db_session.flush()

        for module, dict_module in PERMISSIONS.items():
            for dict_model in dict_module["models"]:
                perm = (
                    db_session.query(PermissionModel)
                    .filter(PermissionModel.model == dict_model["name"])
                    .first()
                )
                if not perm:
                    module_label = dict_module["label"]
                    model_label = dict_model["label"]
                    new_perm_view = PermissionModel(
                        module=module,
                        model=dict_model["name"],
                        action="view",
                        description=f"Permissão de visualizar um(a) {model_label} no módulo {module_label}.",
                    )
                    new_perm_edit = PermissionModel(
                        module=module,
                        model=dict_model["name"],
                        action="edit",
                        description=f"Permissão de editar um(a) {model_label} no módulo {module_label}.",
                    )

                    new_perm_add = PermissionModel(
                        module=module,
                        model=dict_model["name"],
                        action="add",
                        description=f"Permissão de adicionar um(a) {model_label} no módulo {module_label}.",
                    )
                    db_session.add(new_perm_view)
                    db_session.add(new_perm_edit)
                    db_session.add(new_perm_add)
        db_session.commit()
        db_session.flush()

        all_perms = db_session.query(PermissionModel).all()
        for perm in all_perms:
            group_admin.permissions.append(perm)

        db_session.commit()
        db_session.flush()

        new_super_user = UserModel(
            username="agile_admin",
            group_id=group_admin.id,
            password=UserSerivce().get_password_hash(PASSWORD_SUPER_USER),
            email="admin@email.com",
            is_staff=True,
        )
        db_session.add(new_super_user)
        db_session.commit()
        db_session.flush()

        new_super_user.group = group_admin
        db_session.commit()
        db_session.close_all()

    def test_auth_login_sucess(self, setup, create_initial_data):
        """Test login success case"""
        response = self.client.post(
            f"{BASE_API}/auth/login/",
            data={"username": "agile_admin", "password": PASSWORD_SUPER_USER},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@email.com"
        assert "id" in data
        user_id = data["id"]
        token = data["access_token"]
        response = self.client.get(
            f"{BASE_API}/auth/users/{user_id}/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@email.com"
        assert data["id"] == user_id
