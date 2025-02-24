"""Authenticate models"""

from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    func,
)
from sqlalchemy.orm import Mapped, relationship

from src.database import Base
from src.people.models import EmployeeModel

group_permissions = Table(
    "group_permissions",
    Base.metadata,
    Column("group_id", ForeignKey("group.id"), primary_key=True),
    Column("permission_id", ForeignKey("permission.id"), primary_key=True),
)


class PermissionModel(Base):
    """
    Permission model

    Module: lending, people, auth, invoice, log, benfinits
    Method: add, edit, view
    """

    __tablename__ = "permission"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    module = Column("module", String(length=25), nullable=False)
    model = Column("model", String(length=100), nullable=False)
    action = Column("action", String(length=10), nullable=False)
    description = Column("description", String(length=150), nullable=False, default="")

    def __str__(self) -> str:
        return f"{self.module}_{self.model}_{self.action}"


class GroupModel(Base):
    """
    Group model
    """

    __tablename__ = "group"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=50), nullable=False)
    permissions: Mapped[List[PermissionModel]] = relationship(
        secondary=group_permissions,
    )
    created_at = Column(
        "created_at", DateTime, nullable=False, server_default=func.now()
    )
    updated_at = Column(
        "updated_at",
        DateTime,
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
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

    group: Mapped[GroupModel] = relationship()
    group_id = Column("group_id", ForeignKey("group.id"), nullable=True)

    password = Column("password", String(length=255), nullable=False)
    username = Column("username", String(length=255), nullable=False, unique=True)
    email = Column("email", String(length=255), nullable=False, unique=True)
    is_staff = Column("is_staff", Boolean, default=False)
    is_active = Column("is_active", Boolean, default=True)
    last_login_in = Column("last_login", DateTime, nullable=True)
    department = Column("department", String(length=255), nullable=False, default="")
    manager = Column("manager", String(length=255), nullable=False, default="")
    created_at = Column(
        "created_at", DateTime, nullable=False, server_default=func.now()
    )
    updated_at = Column(
        "updated_at",
        DateTime,
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    def __str__(self) -> str:
        return f"{self.email} - {self.group}"


class TokenModel(Base):
    """
    Token model
    """

    __tablename__ = "token"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    user: Mapped[UserModel] = relationship()
    user_id = Column("user_id", ForeignKey("user.id"), nullable=False)

    token = Column("token", String(length=255), unique=True, nullable=False)
    refresh_token = Column(
        "refresh_token", String(length=255), unique=True, nullable=False
    )
    expires_in = Column("expires_in", DateTime, nullable=False)
    refresh_expires_in = Column("refresh_expires_in", DateTime, nullable=False)
