"""Log schemas"""
from pydantic import Field

from src.schemas import BaseSchema


class LogSerializerSchema(BaseSchema):
    """Log serializer schema"""

    id: int
    user: dict
    module: str
    model: str
    operation: str
    identifier: int
    logged_in: str = Field(serialization_alias="loggedIn")
