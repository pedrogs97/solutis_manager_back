"""Inventory models"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from src.database import Base
from src.lending.models import LendingModel
from src.people.models import EmployeeModel
from src.term.models import TermModel


class InventoryModel(Base):
    """
    Inventory model
    """

    __tablename__ = "inventory"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    accepted_term_at = Column("accepted_term_at", DateTime, nullable=True)
    phone = Column("phone", String(11), nullable=True)
    year = Column("year", Integer, nullable=False)
    created_at = Column("created_at", DateTime, default=func.now())

    employee: Mapped[EmployeeModel] = relationship(viewonly=True)
    employee_id = Column("employee_id", ForeignKey(EmployeeModel.id), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{str(self.employee)} - {self.year}"


class InventoryLendingModel(Base):
    """
    Inventory lending model
    """

    __tablename__ = "inventory_lending"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    justification = Column("justification", String(255), nullable=True)
    confirm = Column("confirm", Boolean, default=False)
    created_at = Column("created_at", DateTime, default=func.now())

    inventory: Mapped[InventoryModel] = relationship()
    inventory_id = Column("inventory_id", ForeignKey(InventoryModel.id), nullable=False)
    lending: Mapped[LendingModel] = relationship(viewonly=True)
    lending_id = Column("lending_id", ForeignKey(LendingModel.id), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{str(self.lending)} - {str(self.inventory)}"


class InventoryTermModel(Base):
    """
    Inventory term model
    """

    __tablename__ = "inventory_term"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    justification = Column("justification", String(255), nullable=True)
    confirm = Column("confirm", Boolean, default=False)
    created_at = Column("created_at", DateTime, default=func.now())

    inventory: Mapped[InventoryModel] = relationship()
    inventory_id = Column("inventory_id", ForeignKey(InventoryModel.id), nullable=False)
    term: Mapped[TermModel] = relationship(viewonly=True)
    term_id = Column("term_id", ForeignKey(TermModel.id), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{str(self.term)} - {str(self.inventory)}"


class InventoryExtraAssetModel(Base):
    """
    Inventory extra asset model
    """

    __tablename__ = "inventory_extra_asset"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    register_number = Column("register_number", String(length=255), nullable=True)
    description = Column("description", String(255), nullable=True)
    serial_number = Column("serial_number", String(length=255), nullable=True)
    created_at = Column("created_at", DateTime, default=func.now())

    inventory: Mapped[InventoryModel] = relationship()
    inventory_id = Column("inventory_id", ForeignKey(InventoryModel.id), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.register_number} - {str(self.inventory)}"


class InventoryExtraItemModel(Base):
    """
    Inventory extra item model
    """

    __tablename__ = "inventory_extra_item"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    description = Column("description", String(500), nullable=True)
    created_at = Column("created_at", DateTime, default=func.now())

    inventory: Mapped[InventoryModel] = relationship()
    inventory_id = Column("inventory_id", ForeignKey(InventoryModel.id), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.description} - {str(self.inventory)}"
