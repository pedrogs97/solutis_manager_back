"""Auth schemas"""
from datetime import datetime
from typing import List, Optional

from pydantic import EmailStr, Field, constr

from src.schemas import BaseSchema


class RefreshTokenSchema(BaseSchema):
    """Refresh token schema"""

    refresh_token: str = Field(alias="refreshToken")


class PermissionSchema(BaseSchema):
    """
    Permission schema

    Module: lending, people, auth, invoice, log, benfinits
    Method: add, edit, view
    """

    module: str
    model: str
    action: str


class PermissionSerializerSchema(BaseSchema):
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


class RoleSerializerSchema(BaseSchema):
    """
    Group schema

    GroupModel representation for response
    """

    id: int
    name: str
    permissions: List[PermissionSerializerSchema]


class UserUpdateSchema(BaseSchema):
    """
    User schema

    Used to update
    """

    group: Optional[str] = None
    employee_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    is_staff: Optional[bool] = Field(alias="isStaff", default=None)
    is_active: Optional[bool] = Field(alias="isActive", default=None)


class UserChangePasswordSchema(BaseSchema):
    """
    User change password schema

    Change only password
    """

    password: str
    current_password: str = Field(alias="currentPassword")


class UserSerializerSchema(BaseSchema):
    """
    User serializer

    UserModel representation for response
    """

    id: int
    group: RoleSerializerSchema
    full_name: str = Field(serialization_alias="fullName")
    username: str
    email: str
    is_staff: bool = Field(serialization_alias="isStaff")
    is_active: bool = Field(serialization_alias="isActive")
    last_login_in: Optional[str] = Field(serialization_alias="lastLoginIn")


class NewGroupSchema(BaseSchema):
    """New group schema"""

    name: Optional[str] = None
    permissions: Optional[List[int]] = None


class NewUserSchema(BaseSchema):
    """New user schema"""

    username: constr(to_lower=True, strip_whitespace=True)
    email: EmailStr
    is_staff: bool = Field(
        alias="isStaff", serialization_alias="is_staff", default=False
    )
    is_active: bool = Field(
        alias="isActive", serialization_alias="is_active", default=True
    )
    group: Optional[str] = None
    employee_id: int = Field(alias="employeeId", serialization_alias="employee_id")


class TokenSchema(BaseSchema):
    """Token schema"""

    id: Optional[int]
    user: UserSerializerSchema
    token: str
    expires_in: datetime = Field(serialization_alias="expiresIn")


class NewPasswordSchema(BaseSchema):
    """New password schema"""

    user_id: int = Field(serialization_alias="userId")
