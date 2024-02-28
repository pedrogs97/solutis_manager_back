"""Term models"""


from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from src.database import Base
from src.datasync.models import CostCenterTOTVSModel
from src.document.models import DocumentModel
from src.lending.models import WorkloadModel
from src.people.models import EmployeeModel


class TermStatusModel(Base):
    """
    Term status model

    * Ativo
    * Arquivo de distrato pendente
    * Distrato realizado
    """

    __tablename__ = "term_status"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=40), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.name}"


class TermItemTypeModel(Base):
    """
    Term item type model

    * Kit Ferramenta
    * Fardamento
    """

    __tablename__ = "term_item_type"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(length=40), nullable=False)

    def __str__(self) -> str:
        """Returns model as string"""
        return self.name


class TermItemModel(Base):
    """Term item model"""

    __tablename__ = "term_item"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    description = Column("description", String(length=300))
    size = Column("size", String(length=3), nullable=True)
    quantity = Column("quantity", Integer, nullable=True)
    value = Column("value", Float, nullable=True)
    term: Mapped["TermModel"] = relationship(back_populates="term_item")
    term_id = Column("term_id", ForeignKey("term.id"))

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.id}"


class TermModel(Base):
    """Term model"""

    __tablename__ = "term"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    employee: Mapped[EmployeeModel] = relationship()
    employee_id = Column("employee_id", ForeignKey(EmployeeModel.id), nullable=False)

    document_id = Column("document_id", ForeignKey(DocumentModel.id), nullable=True)
    document: Mapped[DocumentModel] = relationship(foreign_keys=[document_id])

    document_revoke_id = Column(
        "document_revoke_id", ForeignKey(DocumentModel.id), nullable=True
    )
    document_revoke: Mapped[DocumentModel] = relationship(
        foreign_keys=[document_revoke_id]
    )
    # lotação
    workload: Mapped[WorkloadModel] = relationship()
    workload_id = Column("workload_id", ForeignKey(WorkloadModel.id), nullable=True)

    status: Mapped[TermStatusModel] = relationship()
    status_id = Column("status_id", ForeignKey(TermStatusModel.id), nullable=True)

    cost_center: Mapped[CostCenterTOTVSModel] = relationship()
    cost_center_id = Column(
        "cost_center_id", ForeignKey(CostCenterTOTVSModel.id), nullable=False
    )

    type: Mapped[TermItemTypeModel] = relationship()
    type_id = Column("type_id", ForeignKey(TermItemTypeModel.id))

    term_item: Mapped[TermItemModel] = relationship(back_populates="term")
    term_item_id = Column("term_item_id", ForeignKey(TermItemModel.id), nullable=False)

    # código gerado
    number = Column("number", String(length=30), nullable=True)
    manager = Column("manager", String(length=50))
    business_executive = Column("business_executive", String(length=50), nullable=True)
    project = Column("project", String(length=100), nullable=True)
    location = Column("location", String(length=100), nullable=True)
    observations = Column("observations", String(length=255), nullable=True)
    signed_date = Column("signed_date", Date, nullable=True)
    revoke_signed_date = Column("revoke_signed_date", Date, nullable=True)
    glpi_number = Column("glpi_number", String(length=25), nullable=True)

    def __str__(self) -> str:
        """Returns model as string"""
        return f"{self.id} - {self.number} ({self.type.name})"
