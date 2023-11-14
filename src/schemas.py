"""
Base schemas
"""
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")
