"""Inventory schemas"""

from src.schemas import BaseSchema


class EmployeeInventorySerializer(BaseSchema):
    """Employee inventory serializer"""

    registration: str
    birthday: str
