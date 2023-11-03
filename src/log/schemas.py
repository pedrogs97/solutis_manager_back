"""Log schemas"""
from pydantic import Field

from src.auth.schemas import UserSerializerSchema
from src.schemas import BaseSchema


class LogSerializerSchema(BaseSchema):
    """Log serializer schema"""

    id: int
    user: UserSerializerSchema
    module: str
    model: str
    operation: str
    identifier: int
    logged_in: str = Field(serialization_alias="loggedIn")
