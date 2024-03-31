"""Verification models"""

from typing import List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from src.asset.models import AssetTypeModel
from src.database import Base
from src.lending.models import LendingModel


class VerificationCategoryModel(Base):
    """Verification category model

    * Envio
    * Retorno
    """

    __tablename__ = "verification_category"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=150))

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class VerificationModel(Base):
    """Verification model"""

    __tablename__ = "verification"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    asset_type: Mapped[AssetTypeModel] = relationship()
    asset_type_id = Column("asset_type_id", ForeignKey("asset_type.id"), nullable=False)
    category: Mapped[VerificationCategoryModel] = relationship()
    category_id = Column(
        "category_id", ForeignKey("verification_category.id"), nullable=True
    )

    options: Mapped[List["VerificationAnswerOptionModel"]] = relationship()

    question = Column("question", String(length=100))
    step = Column("step", String(length=2))

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.question} ({self.step})"


class VerificationAnswerOptionModel(Base):
    """Verification answer option model"""

    __tablename__ = "verification_answer_option"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    verification: Mapped[VerificationModel] = relationship(viewonly=True)
    verification_id = Column("verification_id", ForeignKey("verification.id"))

    name = Column("name", String(length=100))
    created_at = Column(
        "created_at", DateTime, nullable=False, server_default=func.now()
    )
    updated_at = Column(
        "updated_at",
        DateTime,
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class VerificationTypeModel(Base):
    """Verification type model

    * Envio
    * Retorno
    """

    __tablename__ = "verification_type"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=100))

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class VerificationAnswerModel(Base):
    """Verification answer model"""

    __tablename__ = "verification_answer"

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    lending: Mapped[LendingModel] = relationship()
    lending_id = Column("lending_id", ForeignKey("lending.id"), nullable=False)

    verification: Mapped[VerificationModel] = relationship()
    verification_id = Column("verification_id", ForeignKey("verification.id"))

    type: Mapped[VerificationTypeModel] = relationship()
    type_id = Column("type_id", ForeignKey("verification_type.id"))

    answer = Column("answer", String(length=100), nullable=False)
    observations = Column("observations", String(length=255), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.id}"
