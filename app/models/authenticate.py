"""
Authenticate models
"""
from sqlalchemy import Boolean, String, ForeignKey, Integer, Table, Column
from sqlalchemy.orm import relationship
from app.models.base import Base


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role", ForeignKey("role.id")),
    Column("permission", ForeignKey("permission.id")),
)


class PermissionModel(Base):
    """
    Permission model
    """

    __tablename__ = "permission"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    module = Column("module", String, nullable=False)
    model = Column("model", String, nullable=False)
    method = Column("method", String, nullable=False)


class RoleModel(Base):
    """
    Role model
    """

    __tablename__ = "role"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String, nullable=False)
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        backref="roles",
        back_populates="roles",
    )


class UserModel(Base):
    """
    User model
    """

    __tablename__ = "user"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String, nullable=False)
    full_name = Column("full_name", String, nullable=False)
    password = Column("password", String, nullable=False)
    username = Column("username", String, nullable=False, unique=True)
    email = Column("email", String, nullable=False, unique=True)
    taxpayer_identification = Column(
        "taxpayer_identification", String, nullable=False, unique=True
    )
    is_staff = Column("is_staff", Boolean, default=False)
    is_active = Column("is_active", Boolean, default=True)
    role = relationship("RoleModel")
    role_id = Column("role_id", ForeignKey("roles.id"), nullable=False)
