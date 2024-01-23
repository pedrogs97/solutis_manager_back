"""Lending schemas"""
from typing import List, Optional

from pydantic import Field

from src.schemas import BaseSchema


class NewVerificationSchema(BaseSchema):
    """New verification schema"""

    question: str
    step: str
    category: str
    asset_type_id: int = Field(alias="assetTypeId")
    options: List[str]


class VerificationSerializerSchema(BaseSchema):
    """Verification serializer schema"""

    id: int
    question: str
    step: str
    category: Optional[str] = None
    asset_type: str = Field(serialization_alias="assetType")
    options: Optional[List[str]] = []


class VerificationTypeSerializerSchema(BaseSchema):
    """
    Verification type serializer schema

    * Saída - envio para o colaborador
    * Retorno - envio para a empresa
    """

    id: int
    name: str


class VerificationCategorySerializerSchema(BaseSchema):
    """
    Verification category serializer schema
    """

    id: int
    name: str


class NewAnswersSchema(BaseSchema):
    """Answers schema"""

    verification_id: int = Field(alias="verificationId")
    answer: str
    observations: Optional[str] = None


class NewVerificationAnswerSchema(BaseSchema):
    """New verification answer schema"""

    lending_id: int = Field(alias="lendingId")
    type_id: int = Field(alias="typeId")
    answered: List[NewAnswersSchema]


class VerificationAnswerSerializerSchema(BaseSchema):
    """Verification answer serializer schema"""

    id: int
    lending_id: int = Field(serialization_alias="lendingId")
    verification: VerificationSerializerSchema
    type: VerificationTypeSerializerSchema
    answer: str
    observations: Optional[str] = None
