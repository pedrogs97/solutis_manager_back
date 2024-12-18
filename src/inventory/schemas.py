"""Inventory schemas"""

from typing import List, Optional

from pydantic import Field, model_validator

from src.schemas import BaseSchema


class EmployeeInventorySerializer(BaseSchema):
    """Employee inventory serializer"""

    registration: str
    birthday: str


class AnswerInventoryLendingSerializer(BaseSchema):
    """Inventory lending serializer"""

    justification: Optional[str] = None
    confirm: bool
    lending_id: int = Field(alias="lendingId")

    @model_validator(mode="before")
    @classmethod
    def validate_justification_based_on_confirm(cls, values: dict):
        """Validate justification based on confirm"""
        justification = values.get("justification")
        confirm = values.get("confirm", False)

        if not confirm and not justification:
            raise ValueError("Preencha a justificativa")

        return values


class AnswerInventoryTermSerializer(BaseSchema):
    """Inventory term serializer"""

    justification: Optional[str] = None
    confirm: bool
    term_id: int = Field(alias="termId")

    @model_validator(mode="before")
    @classmethod
    def validate_justification_based_on_confirm(cls, values: dict):
        """Validate justification based on confirm"""
        justification = values.get("justification")
        confirm = values.get("confirm", False)

        if not confirm and not justification:
            raise ValueError("Preencha a justificativa")

        return values


class AnswerInventoryExtraAssetSerializer(BaseSchema):
    """Answer inventory extra asset serializer"""

    register_number: str = Field(alias="registerNumber")
    description: str
    serial_number: str = Field(alias="serialNumber")


class AnswerInventoryExtraItemSerializer(BaseSchema):
    """Answer inventory extra item serializer"""

    description: str


class AnswerInventorySerializer(BaseSchema):
    """Answer inventory serializer"""

    phone: str
    lendings: List[AnswerInventoryLendingSerializer] = []
    terms: List[AnswerInventoryTermSerializer] = []
    extra_assets: List[AnswerInventoryExtraAssetSerializer] = Field(
        alias="extraAssets", default=[]
    )
    extra_items: Optional[str] = Field(alias="extraItems")
