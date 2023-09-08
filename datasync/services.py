"""Methods to access database"""
import logging
from datetime import date, datetime
from sqlalchemy.sql import or_
from sqlalchemy.exc import IntegrityError
from pydantic_core import ValidationError
from datasync.db.connection import get_db_session
from datasync.models.sync import SyncModel
from datasync.models.employee import (
    EmployeeModel,
    EmployeeMatrimonialStatusModel,
    EmployeeGenderModel,
    EmployeeNationalityModel,
)
from datasync.schemas.employee import (
    EmployeeSchema,
    EmployeeGenderSchema,
    EmployeeMatrimonialStatusSchema,
    EmployeeNationalitySchema,
)
from datasync.schemas.base import BaseSchema


logger = logging.getLogger(__name__)


def set_last_sync(count_new_values: int, elapsed_time: float, model: str) -> None:
    """Set last sync in database"""
    try:
        last_sync = SyncModel(
            count_new_values=count_new_values, execution_time=elapsed_time, model=model
        )
        db_session = get_db_session()
        if not db_session:
            logger.warning("No db session.")
            return
        db_session.add(last_sync)
        db_session.commit()
        db_session.close()
    except TypeError as err:
        logger.warning("Error: %s", err.args[0])


def totvs_to_employee_schema(
    row,
) -> EmployeeSchema | None:
    """Convert data from TOTVS to EmployeeSchema

    From
    CODIGO, NOME, DTNASCIMENTO, ESTADOCIVIL, SEXO, NACIONALIDADE,\
    RUA, NUMERO, COMPLEMENTO, BAIRRO, ESTADO, CIDADE, CEP, PAIS, CPF, TELEFONE1,\
    CARTIDENTIDADE, UFCARTIDENT, ORGEMISSORIDENT, DTEMISSAOIDENT, EMAIL
    """
    try:
        address = f"{row[6]}, {row[7]}, {row[8]}, {row[9]}. \
            {row[11]} - {row[10]}, {row[13]}. {row[12]}"
        birthday_datetime: datetime = row[2]
        return EmployeeSchema(
            Id=None,
            Code=row[0] if row[0] is not None else "",
            FullName=row[1] if row[1] is not None else "",
            Birthday=birthday_datetime.date(),
            MaritalStatus=row[3] if row[3] is not None else "",
            Gender=row[4] if row[4] is not None else "",
            Nationality=row[5] if row[5] is not None else "",
            Address=address,
            TaxpayerIdentification=row[14] if row[14] is not None else "",
            CellPhone=row[15] if row[15] is not None else "",
            NacionalIdentification=row[16] if row[16] is not None else "",
            Email=row[20] if row[20] is not None else "",
            Role="",
            Manager="",
            CostCenterNumber="",
            CostCenterName="",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_matrimonial_status_schema(
    row,
) -> EmployeeMatrimonialStatusSchema | None:
    """Convert data from TOTVS to EmployeeMatrimonialStatusSchema

    From
    DESCRICAO, CODINTERNO
    """
    try:
        return EmployeeMatrimonialStatusSchema(
            Id=None,
            Code=row[1] if row[1] is not None else "",
            Description=row[1] if row[1] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_gender_schema(
    row,
) -> EmployeeGenderSchema | None:
    """Convert data from TOTVS to EmployeeGenderSchema

    From
    DESCRICAO, CODINTERNO
    """
    try:
        return EmployeeGenderSchema(
            Id=None,
            Code=row[1] if row[1] is not None else "",
            Description=row[1] if row[1] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_nationality_schema(
    row,
) -> EmployeeNationalitySchema | None:
    """Convert data from TOTVS to EmployeeNationalitySchema

    From
    DESCRICAO, CODINTERNO
    """
    try:
        return EmployeeNationalitySchema(
            Id=None,
            Code=row[1] if row[1] is not None else "",
            Description=row[1] if row[1] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def get_checksum(schema: BaseSchema) -> bytes:
    """Returns EmployeeSchema as bytes"""
    schema_dict = schema.model_dump(by_alias=False, exclude={"id"})
    values = schema_dict.values()
    bytes_schema = bytes(0)
    for item in values:
        if isinstance(item, date):
            bytes_schema += bytes(item.isoformat(), "utf-8")
        else:
            bytes_schema += bytes(str(item), "utf-8")
    return bytes


def verify_changes_empolyee(employee: EmployeeSchema) -> bool:
    """
    Check if the EmployeeSchema object is different from the EmployeSchema in the database.
    Returns True if it does not exist in the database.
    """
    checksum_from_totvs = get_checksum(employee)
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    employee_db = db_session.query(EmployeeModel).filter_by(code=employee.code).first()
    db_session.close()
    if not employee_db:
        return True

    return get_checksum(employee_db.to_schema()) != checksum_from_totvs


def verify_changes_matrimonial_status(
    employee: EmployeeMatrimonialStatusSchema,
) -> bool:
    """
    Check if the EmployeeMatrimonialStatusSchema object is different from the EmployeSchema in the database.
    Returns True if it does not exist in the database.
    """
    checksum_from_totvs = get_checksum(employee)
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    employee_db = (
        db_session.query(EmployeeMatrimonialStatusModel)
        .filter_by(code=employee.code)
        .first()
    )
    db_session.close()
    if not employee_db:
        return True

    return get_checksum(employee_db.to_schema()) != checksum_from_totvs


def verify_changes_gender(employee: EmployeeGenderSchema) -> bool:
    """
    Check if the EmployeeGenderSchema object is different from the EmployeSchema in the database.
    Returns True if it does not exist in the database.
    """
    checksum_from_totvs = get_checksum(employee)
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    employee_db = (
        db_session.query(EmployeeGenderModel).filter_by(code=employee.code).first()
    )
    db_session.close()
    if not employee_db:
        return True

    return get_checksum(employee_db.to_schema()) != checksum_from_totvs


def verify_changes_nationality(employee: EmployeeNationalitySchema) -> bool:
    """
    Check if the EmployeeSchema object is different from the EmployeSchema in the database.
    Returns True if it does not exist in the database.
    """
    checksum_from_totvs = get_checksum(employee)
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    nacionality_db = (
        db_session.query(EmployeeNationalityModel).filter_by(code=employee.code).first()
    )
    db_session.close()
    if not nacionality_db:
        return True

    return get_checksum(nacionality_db.to_schema()) != checksum_from_totvs


def insert_employee(employee: EmployeeSchema) -> None:
    """Inserts new or changed employee"""
    try:
        new_employee = EmployeeModel(**employee.model_dump(by_alias=False))
        db_session = get_db_session()
        if not db_session:
            logger.warning("No db session.")
            return
        employee_db = (
            db_session.query(EmployeeModel)
            .filter(
                or_(
                    EmployeeModel.code == employee.code,
                    EmployeeModel.taxpayer_identification
                    == employee.taxpayer_identification,
                )
            )
            .first()
        )
        if employee_db:
            logger.info("Updating: %s", str(employee_db))
            db_session.delete(employee_db)
            db_session.commit()
        else:
            logger.info("New: %s", str(new_employee))

        db_session.add(new_employee)
        db_session.commit()
        db_session.close()
    except IntegrityError as err:
        logger.warning("Error: %s", err.args[0])
        if db_session:
            db_session.close()


def insert_matrimonial_status(
    matrimonial_status: EmployeeMatrimonialStatusSchema,
) -> None:
    """Inserts new matrimonial status"""
    try:
        new_matrimonial_status = EmployeeMatrimonialStatusModel(
            **matrimonial_status.model_dump(by_alias=False)
        )
        db_session = get_db_session()
        if not db_session:
            logger.warning("No db session.")
            return

        logger.info("New: %s", str(new_matrimonial_status))

        db_session.add(new_matrimonial_status)
        db_session.commit()
    except IntegrityError as err:
        logger.warning("Error: %s", err.args[0])

    if db_session:
        db_session.close()


def insert_gender(gender: EmployeeGenderSchema) -> None:
    """Inserts new gender"""
    try:
        new_gender = EmployeeGenderModel(**gender.model_dump(by_alias=False))
        db_session = get_db_session()
        if not db_session:
            logger.warning("No db session.")
            return

        logger.info("New: %s", str(new_gender))
        db_session.add(new_gender)
        db_session.commit()
    except IntegrityError as err:
        logger.warning("Error: %s", err.args[0])

    if db_session:
        db_session.close()


def insert_nationality(nacionality: EmployeeNationalitySchema) -> None:
    """Inserts new nacionality"""
    try:
        new_nationality = EmployeeNationalityModel(
            **nacionality.model_dump(by_alias=False)
        )
        db_session = get_db_session()
        if not db_session:
            logger.warning("No db session.")
            return

        logger.info("New: %s", str(new_nationality))
        db_session.add(new_nationality)
        db_session.commit()
    except IntegrityError as err:
        logger.warning("Error: %s", err.args[0])

    if db_session:
        db_session.close()
