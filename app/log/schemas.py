"""Log schemas"""
from pydantic import Field
from app.schemas import BaseSchema
from app.auth.schemas import UserSerializer


class LogSerializerSchema(BaseSchema):
    """Log serializer schema"""

    id: int
    user: UserSerializer
    module: str
    model: str
    operation: str
    identifier: int
    logged_in: str = Field(serialization_alias="loggedIn")
