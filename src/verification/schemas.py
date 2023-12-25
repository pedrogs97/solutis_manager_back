"""Lending schemas"""
from typing import Optional

from pydantic import Field

from src.schemas import BaseSchema


class NewVerificationSchema(BaseSchema):
    """New verification schema"""

    question: str
    step: str
    asset_type_id: int = Field(alias="assetTypeId")


class VerificationSerializerSchema(BaseSchema):
    """Verification serializer schema"""

    id: int
    question: str
    step: str
    asset_type: str = Field(serialization_alias="assetType")


class VerificationTypeSerializerSchema(BaseSchema):
    """
    Verification type serializer schema

    * Saída - envio para o colaborador
    * Retorno - envio para a empresa
    """

    id: int
    name: str


class NewVerificationAnswerSchema(BaseSchema):
    """New verification answer schema"""

    lending_id: int = Field(alias="lendingId")
    verification_id: int = Field(alias="verificationId")
    type_id: int = Field(alias="typeId")
    answer: str
    observations: Optional[str] = None


class VerificationAnswerSerializerSchema(BaseSchema):
    """Verification answer serializer schema"""

    id: int
    lending_id: int = Field(serialization_alias="lendingId")
    verification: VerificationSerializerSchema
    type: VerificationTypeSerializerSchema
    answer: str
    observations: Optional[str] = None
