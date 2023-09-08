"""
Base schemas
"""
from pydantic import BaseModel, ConfigDict


def _to_camel(string: str) -> str:
    return "".join(word.capitalize() for word in string.split("_"))


class BaseSchema(BaseModel):
    """Base schema"""

    model_config = ConfigDict(alias_generator=_to_camel, str_strip_whitespace=True)
