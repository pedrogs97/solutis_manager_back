"""Authenticate models"""
from typing import List
from sqlalchemy import Boolean, String, ForeignKey, Integer, Table, Column, DateTime
from sqlalchemy.orm import relationship, Mapped
from app.database import Base
from app.people.models import EmployeeModel


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("role.id")),
    Column("permission_id", ForeignKey("permission.id")),
)


class PermissionModel(Base):
    """
    Permission model

    Module: lending, people, auth, invoice, log, benfinits
    Method: add, edit, view
    """

    __tablename__ = "permission"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    module = Column("module", String, nullable=False)
    model = Column("model", String, nullable=False)
    action = Column("action", String, nullable=False)
    description = Column("description", String(length=150), nullable=False, default="")

    def __str__(self) -> str:
        return f"{self.module}_{self.model}_{self.action}"


class RoleModel(Base):
    """
    Role model
    """

    __tablename__ = "role"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String, nullable=False)
    permissions: Mapped[List[PermissionModel]] = relationship(
        secondary=role_permissions,
    )

    def __str__(self) -> str:
        return str(self.name)


class UserModel(Base):
    """
    User model
    """

    __tablename__ = "user"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    employee: Mapped[EmployeeModel] = relationship()
    employee_id = Column("employee_id", ForeignKey("employees.id"), nullable=True)

    role: Mapped[RoleModel] = relationship()
    role_id = Column("role_id", ForeignKey("role.id"), nullable=False)

    full_name = Column("full_name", String, nullable=False)
    password = Column("password", String, nullable=False)
    username = Column("username", String, nullable=False, unique=True)
    email = Column("email", String, nullable=False, unique=True)
    taxpayer_identification = Column(
        "taxpayer_identification", String(length=14), nullable=False, unique=True
    )
    is_staff = Column("is_staff", Boolean, default=False)
    is_active = Column("is_active", Boolean, default=True)
    last_login_in = Column("last_login", DateTime, nullable=True)

    def __str__(self) -> str:
        return f"{self.email} - {self.role}"


class TokenModel(Base):
    """
    Token model
    """

    __tablename__ = "token"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    user: Mapped[UserModel] = relationship()
    user_id = Column("user_id", ForeignKey("user.id"), nullable=False)

    token = Column("token", String, unique=True, nullable=False)
    expires_in = Column("expires_in", DateTime, nullable=False)
