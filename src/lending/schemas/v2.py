"""Lending schemas v2"""

from typing import List, Optional

from pydantic import BaseModel, Field

from src.lending.enums import LendingBUEnum


class NewAnswersDataSchema(BaseModel):
    """Answers schema"""

    verification_id: int = Field(alias="verificationId")
    answer: str
    observations: Optional[str] = None


class NewVerificationAnswerDataSchema(BaseModel):
    """Schema for incoming verification answer data"""

    type_id: int = Field(alias="typeId")
    answered: List[NewAnswersDataSchema]


class NewLendingDataSchema(BaseModel):
    """Schema for incoming lending data"""

    employee_id: int = Field(alias="employeeId")
    asset_id: int = Field(alias="assetId")
    workload_id: Optional[int] = Field(alias="workloadId", default=None)
    witnesses_id: Optional[List[int]] = Field(alias="witnessesId", default=[])
    cost_center_id: int = Field(alias="costCenterId")
    manager: str
    observations: Optional[str] = None
    glpi_number: Optional[str] = Field(alias="glpiNumber", default=None)
    project: Optional[str] = None
    business_executive: Optional[str] = Field(alias="businessExecutive", default=None)
    location: str
    bu: LendingBUEnum
    ms_office: bool = Field(alias="msOffice", default=False)
    principal_signer: str = Field(alias="principalSigner")
    employee_signer: str = Field(alias="employeeSigner")
    legal_person: Optional[bool] = Field(alias="legalPerson", default=False)
    verification_answers: Optional[NewVerificationAnswerDataSchema] = Field(
        alias="verificationAnswers", default=None
    )
