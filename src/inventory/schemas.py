"""Inventory schemas"""

from typing import List, Optional

from pydantic import Field

from src.schemas import BaseSchema


class EmployeeInventorySerializer(BaseSchema):
    """Employee inventory serializer"""

    registration: str
    birthday: str


class AnswerInventoryLendingSerializer(BaseSchema):
    """Inventory lending serializer"""

    justification: Optional[str]
    confirm: bool
    lending_id: int = Field(alias="lendingId")

    # @model_validator
    # @classmethod
    # def validate_justification_based_on_confirm(cls, values: dict):
    #     """Validate justification based on confirm"""
    #     justification = values.get("justification")
    #     confirm = values.get("confirm")

    #     if confirm and not justification:
    #         raise ValueError("Justification must be provided if confirm is true")

    #     return values


class AnswerInventoryTermSerializer(BaseSchema):
    """Inventory term serializer"""

    justification: Optional[str]
    confirm: bool
    term_id: int = Field(alias="termId")

    # @model_validator
    # @classmethod
    # def validate_justification_based_on_confirm(cls, values: dict):
    #     """Validate justification based on confirm"""
    #     justification = values.get("justification")
    #     confirm = values.get("confirm")

    #     if confirm and not justification:
    #         raise ValueError("Justification must be provided if confirm is true")

    #     return values


class AnswerInventoryExtraAssetSerializer(BaseSchema):
    """Answer inventory extra asset serializer"""

    id: int
    register_number: str = Field(alias="registerNumber")
    description: str
    serial_number: str = Field(alias="serialNumber")


class AnswerInventoryExtraItemSerializer(BaseSchema):
    """Answer inventory extra item serializer"""

    description: str


class AnswerInventorySerializer(BaseSchema):
    """Answer inventory serializer"""

    accepted_term_at: str = Field(default=False, alias="acceptedTermAt")
    phone: Optional[str]
    lendings: List[AnswerInventoryLendingSerializer] = []
    terms: List[AnswerInventoryTermSerializer] = []
    extra_assets: List[AnswerInventoryExtraAssetSerializer] = []
    extra_items: List[AnswerInventoryExtraItemSerializer] = []
