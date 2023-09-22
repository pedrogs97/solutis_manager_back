"""Auth schemas"""
from datetime import datetime
from typing import List, Optional
from pydantic import Field, EmailStr, constr
from app.schemas import BaseSchema


class PermissionSchema(BaseSchema):
    """
    Permission schema

    Module: lending, people, auth, invoice, log, benfinits
    Method: add, edit, view
    """

    module: str
    model: str
    action: str


class PermissionSerializer(BaseSchema):
    """
    Permission serializer

    PermissionModel representation for response

    Module: lending, people, auth, invoice, log, benfinits
    Method: add, edit, view
    """

    id: int
    module: str
    model: str
    action: str
    description: str


class RoleSerializer(BaseSchema):
    """
    Role schema

    RoleModel representation for response
    """

    id: int
    name: str
    permissions: List[PermissionSerializer]


class UserUpdateSchema(BaseSchema):
    """
    User schema

    Used to update
    """

    role: Optional[str] = None
    full_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    taxpayer_identification: Optional[str] = None
    is_staff: Optional[bool] = None
    is_active: Optional[bool] = None


class UserSerializer(BaseSchema):
    """
    User serializer

    UserModel representation for response
    """

    id: int
    role: RoleSerializer
    full_name: str = Field(serialization_alias="fullName")
    username: str
    email: str
    taxpayer_identification: str = Field(serialization_alias="taxpayerIdentification")
    is_staff: bool = Field(serialization_alias="isStaff")
    is_active: bool = Field(serialization_alias="isActive")
    last_login_in: Optional[str] = Field(serialization_alias="lastLoginIn")


class RoleSchema(BaseSchema):
    """Role schema"""

    name: str
    permissions: List[PermissionSchema]


class NewRoleSchema(BaseSchema):
    """New role schema"""

    name: Optional[str] = None
    permissions: Optional[List[int]] = None


class LoginSchema(BaseSchema):
    """Login schema"""

    username: str
    password: str


class NewUserSchema(BaseSchema):
    """New user schema"""

    full_name: str
    username: constr(to_lower=True, strip_whitespace=True)
    email: EmailStr
    taxpayer_identification: str = Field(max_length=14)
    is_staff: bool
    is_active: bool
    role: str


class TokenSchema(BaseSchema):
    """Token schema"""

    id: Optional[int]
    user: UserSerializer
    token: str
    expires_in: datetime = Field(serialization_alias="expiresIn")


class NewPasswordSchema(BaseSchema):
    """New password schema"""

    user_id: int
