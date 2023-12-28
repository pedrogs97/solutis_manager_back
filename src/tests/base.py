"""Base test"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth.models import GroupModel, PermissionModel, UserModel
from src.auth.service import UserSerivce
from src.backends import get_db_session
from src.config import (
    PASSWORD_SUPER_USER,
    PERMISSIONS,
    get_database_server_url,
    get_database_url,
)
from src.database import Base
from src.main import app
from src.people.models import (
    EmployeeGenderModel,
    EmployeeMaritalStatusModel,
    EmployeeModel,
    EmployeeNationalityModel,
    EmployeeRoleModel,
)


class TestBase:
    """
    Base test

    This class provides base setup and initial data for all tests
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
    def create_super_user(self):
        """Creates super user for test"""
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

    @pytest.fixture
    def create_base_employee(self):
        """Create base employee for test"""
        db_session = self.testing_session_local()
        base_nationality = EmployeeNationalityModel(code="BR", description="Brasil")
        base_marital_status = EmployeeMaritalStatusModel(code="C", description="Casado")
        base_gender = EmployeeGenderModel(code="M", description="Masculino")
        base_role = EmployeeRoleModel(code="ADS", name="Analista de Sistemas")

        db_session.add(base_gender)
        db_session.add(base_marital_status)
        db_session.add(base_nationality)
        db_session.add(base_role)
        db_session.commit()
        db_session.flush()

        employee = EmployeeModel(
            role=base_role,
            nationality=base_nationality,
            marital_status=base_marital_status,
            gender=base_gender,
            code="1111111111",
            full_name="Colaborador Base Teste",
            taxpayer_identification="11111111111",
            national_identification="111111111111111",
            address="endereço",
            cell_phone="111111111111111",
            email="base@email.com",
            birthday=datetime.now().date(),
            manager="Gestor",
            admission_date=datetime.now().date(),
            registration="1111111111111111",
        )

        db_session.add(employee)
        db_session.commit()
        db_session.flush()

    @pytest.fixture
    def create_initial_data(self, setup, create_super_user, create_base_employee):
        """Create initial data for test"""
        print("Data created")
