"""Methods to access database"""
import logging
from datetime import date, datetime
from sqlalchemy.sql import or_
from sqlalchemy.exc import IntegrityError
from pydantic_core import ValidationError
from datasync.database import get_db_session
from datasync.models import (
    AssetModel,
    AssetTypeModel,
    CostCenterModel,
    EmployeeModel,
    EmployeeGenderModel,
    EmployeeMatrimonialStatusModel,
    EmployeeNationalityModel,
    EmployeeRoleModel,
    SyncModel,
)
from datasync.schemas import (
    AssetTotvsSchema,
    AssetTypeTotvsSchema,
    BaseSchema,
    CostCenterTotvsSchema,
    EmployeeTotvsSchema,
    EmployeeGenderTotvsSchema,
    EmployeeMatrimonialStatusTotvsSchema,
    EmployeeNationalityTotvsSchema,
    EmployeeRoleTotvsSchema,
)


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
) -> EmployeeTotvsSchema | None:
    """Convert data from TOTVS to EmployeeTotvsSchema

    From
    CODIGO, NOME, DTNASCIMENTO, CIVIL, SEXO , NACIONALIDADE, RUA,
    NUMERO, COMPLEMENTO, BAIRRO, ESTADO, CIDADE, CEP, PAIS, CPF,
    TELEFONE1, CARTIDENTIDADE, UFCARTIDENT, ORGEMISSORIDENT, DTEMISSAOIDENT,
    EMAIL, CARGO
    """
    try:
        address = f"{row[6]}, {row[7]}, {row[8]}, {row[9]}. \
            {row[11]} - {row[10]}, {row[13]}. {row[12]}"
        birthday_datetime: datetime = row[2]
        return EmployeeTotvsSchema(
            id=None,
            code=row[0] if row[0] is not None else "",
            full_name=row[1] if row[1] is not None else "",
            birthday=birthday_datetime.date(),
            taxpayer_identification=row[14] if row[14] is not None else "",
            nacional_identification=row[16] if row[16] is not None else "",
            matrimonial_status=row[3] if row[3] is not None else "",
            nationality=row[5] if row[5] is not None else "",
            role=row[21] if row[21] is not None else "",
            address=address,
            cell_phone=row[15] if row[15] is not None else "",
            email=row[20] if row[20] is not None else "",
            gender=row[4] if row[4] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_matrimonial_status_schema(
    row,
) -> EmployeeMatrimonialStatusTotvsSchema | None:
    """Convert data from TOTVS to EmployeeMatrimonialStatusTotvsSchema

    From
    DESCRICAO, CODINTERNO
    """
    try:
        return EmployeeMatrimonialStatusTotvsSchema(
            id=None,
            code=row[1] if row[1] is not None else "",
            description=row[0] if row[0] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_gender_schema(
    row,
) -> EmployeeGenderTotvsSchema | None:
    """Convert data from TOTVS to EmployeeGenderTotvsSchema

    From
    DESCRICAO, CODINTERNO
    """
    try:
        return EmployeeGenderTotvsSchema(
            id=None,
            code=row[1] if row[1] is not None else "",
            description=row[0] if row[0] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_nationality_schema(
    row,
) -> EmployeeNationalityTotvsSchema | None:
    """Convert data from TOTVS to EmployeeNationalityTotvsSchema

    From
    DESCRICAO, CODINTERNO
    """
    try:
        return EmployeeNationalityTotvsSchema(
            id=None,
            code=row[1] if row[1] is not None else "",
            description=row[0] if row[0] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_cost_center_schema(
    row,
) -> CostCenterTotvsSchema | None:
    """Convert data from TOTVS to CostCenterTotvsSchema

    From
    CODREDUZIDO, NOME, DESCRICAO
    """
    try:
        return CostCenterTotvsSchema(
            id=None,
            code=row[0] if row[0] is not None else "",
            name=row[1] if row[1] is not None else "",
            classification=row[2] if row[2] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_asset_type_schema(
    row,
) -> AssetTypeTotvsSchema | None:
    """Convert data from TOTVS to AssetTypeTotvsSchema

    From
    IDGRUPOPATRIMONIO, CODGRUPOPATRIMONIO, DESCRICAO
    """
    try:
        return AssetTypeTotvsSchema(
            id=None,
            code=row[0] if row[0] is not None else "",
            group_code=row[1] if row[1] is not None else "",
            name=row[2] if row[2] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_asset_schema(
    row,
) -> AssetTotvsSchema | None:
    """Convert data from TOTVS to AssetTotvsSchema

    From
    IDPATRIMONIO, DESCRICAO, TIPO,
    ATIVO, DATAAQUISICAO, PATRIMONIO, QUANTIDADE, UNIDADE, OBSERVACOES,
    CODIGOBARRA, CENTROCUSTO, VALORBASE, VRDEPACUCORRIGIDA, SERIE,
    IMEI, ACESSORIOS, OPERADORA, SISTEMAOPERACIONAL, PACOTEOFFICE,
    PADRAOEQUIP, GARANTIA, LINHA, FORNECEDOR
    """
    try:
        acquisition_date: datetime = row[4]
        assurance_date: datetime = row[19]
        ms_office = None
        if row[18] is not None:
            ms_office = row[18] == "SIM"

        return AssetTotvsSchema(
            code=row[0] if row[0] is not None else "",
            description=row[1] if row[1] is not None else "",
            type=row[2] if row[2] is not None else "",
            active=row[3] if row[3] is not None else "",
            acquisition_date=acquisition_date,
            register_number=row[5] if row[5] is not None else "",
            quantity=row[6] if row[6] is not None else "",
            unit=row[7] if row[7] is not None else "",
            observations=row[8] if row[8] is not None else "",
            cost_center=row[10] if row[10] is not None else "",
            value=row[11] if row[11] is not None else 0.0,
            serial_number=row[13] if row[13] is not None else "",
            imei=row[14] if row[14] is not None else "",
            accessories=row[15] if row[15] is not None else "",
            operator=row[16] if row[16] is not None else "",
            operational_system=row[17] if row[17] is not None else "",
            ms_office=ms_office,
            pattern=row[18] if row[18] is not None else "",
            assurance_date=assurance_date,
            line_number=row[20] if row[20] is not None else "",
            supplier=row[21] if row[21] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_role_schema(
    row,
) -> EmployeeRoleTotvsSchema | None:
    """Convert data from TOTVS to EmployeeRoleTotvsSchema

    From
    CODIGO, NOME
    """
    try:
        return EmployeeRoleTotvsSchema(
            code=row[0] if row[0] is not None else "",
            name=row[1] if row[1] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def get_checksum(schema: BaseSchema) -> bytes:
    """Returns EmployeeTotvsSchema as bytes"""
    schema_dict = schema.model_dump()
    values = schema_dict.values()
    bytes_schema = bytes(0)
    for item in values:
        if isinstance(item, date):
            bytes_schema += bytes(item.isoformat(), "utf-8")
        else:
            bytes_schema += bytes(str(item), "utf-8")
    return bytes_schema


def verify_changes_empolyee(employee: EmployeeTotvsSchema) -> bool:
    """
    Check if the EmployeeTotvsSchema object is different from the EmployeSchema in the database.
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

    return (
        get_checksum(EmployeeTotvsSchema(**employee_db.__dict__)) != checksum_from_totvs
    )


def verify_changes_matrimonial_status(
    matrimonial_status: EmployeeMatrimonialStatusTotvsSchema,
) -> bool:
    """
    Check if the EmployeeMatrimonialStatusTotvsSchema object \
        is different from the EmployeeMatrimonialStatusTotvsSchema in the database.
    Returns True if it does not exist in the database.
    """
    checksum_from_totvs = get_checksum(matrimonial_status)
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    matrimonial_status_db = (
        db_session.query(EmployeeMatrimonialStatusModel)
        .filter_by(code=matrimonial_status.code)
        .first()
    )
    db_session.close()
    if not matrimonial_status_db:
        return True

    return (
        get_checksum(
            EmployeeMatrimonialStatusTotvsSchema(**matrimonial_status_db.__dict__)
        )
        != checksum_from_totvs
    )


def verify_changes_gender(gender: EmployeeGenderTotvsSchema) -> bool:
    """
    Check if the EmployeeGenderTotvsSchema object is different from the EmployeeGenderTotvsSchema in the database.
    Returns True if it does not exist in the database.
    """
    checksum_from_totvs = get_checksum(gender)
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    employee_db = (
        db_session.query(EmployeeGenderModel).filter_by(code=gender.code).first()
    )
    db_session.close()
    if not employee_db:
        return True

    return (
        get_checksum(EmployeeGenderTotvsSchema(**employee_db.__dict__))
        != checksum_from_totvs
    )


def verify_changes_nationality(nationality: EmployeeNationalityTotvsSchema) -> bool:
    """
    Check if the EmployeeNationalityTotvsSchema object is different from the EmployeeNationalityTotvsSchema in the database.
    Returns True if it does not exist in the database.
    """
    checksum_from_totvs = get_checksum(nationality)
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    nacionality_db = (
        db_session.query(EmployeeNationalityModel)
        .filter_by(code=nationality.code)
        .first()
    )
    db_session.close()
    if not nacionality_db:
        return True

    return (
        get_checksum(EmployeeNationalityTotvsSchema(**nacionality_db.__dict__))
        != checksum_from_totvs
    )


def verify_changes_cost_center(cost_center: EmployeeNationalityTotvsSchema) -> bool:
    """
    Check if the CostCenterTotvsSchema object is different from the CostCenterTotvsSchema in the database.
    Returns True if it does not exist in the database.
    """
    checksum_from_totvs = get_checksum(cost_center)
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    cost_center_db = (
        db_session.query(CostCenterModel).filter_by(code=cost_center.code).first()
    )
    db_session.close()
    if not cost_center_db:
        return True

    return (
        get_checksum(CostCenterTotvsSchema(**cost_center_db.__dict__))
        != checksum_from_totvs
    )


def verify_changes_asset_type(asset_type: AssetTypeTotvsSchema) -> bool:
    """
    Check if the AssetTypeTotvsSchema object is different
    from the AssetTypeTotvsSchema in the database.

    Returns True if it does not exist in the database.
    """
    checksum_from_totvs = get_checksum(asset_type)
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    asset_type_db = (
        db_session.query(AssetTypeModel).filter_by(code=asset_type.code).first()
    )
    db_session.close()
    if not asset_type_db:
        return True

    return (
        get_checksum(AssetTypeTotvsSchema(**asset_type_db.__dict__))
        != checksum_from_totvs
    )


def verify_changes_asset(asset: AssetTotvsSchema) -> bool:
    """
    Check if the AssetTotvsSchema object is different from the AssetTotvsSchema in the database.
    Returns True if it does not exist in the database.
    """
    checksum_from_totvs = get_checksum(asset)
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    asset_db = db_session.query(AssetModel).filter_by(code=asset.code).first()
    db_session.close()
    if not asset_db:
        return True

    return get_checksum(AssetTotvsSchema(**asset_db.__dict__)) != checksum_from_totvs


def verify_changes_role(role: EmployeeRoleTotvsSchema) -> bool:
    """
    Check if the EmployeeRoleTotvsSchema object is different
    from the EmployeeRoleTotvsSchema in the database.

    Returns True if it does not exist in the database.
    """
    checksum_from_totvs = get_checksum(role)
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    role_db = db_session.query(AssetModel).filter_by(code=role.code).first()
    db_session.close()
    if not role_db:
        return True

    return (
        get_checksum(EmployeeRoleTotvsSchema(**role_db.__dict__)) != checksum_from_totvs
    )


def insert_employee(employee: EmployeeTotvsSchema) -> None:
    """Inserts new or changed employee"""
    try:
        new_employee = EmployeeModel(**employee.model_dump())
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
    matrimonial_status: EmployeeMatrimonialStatusTotvsSchema,
) -> None:
    """Inserts new matrimonial status"""
    try:
        new_matrimonial_status = EmployeeMatrimonialStatusModel(
            **matrimonial_status.model_dump()
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


def insert_gender(gender: EmployeeGenderTotvsSchema) -> None:
    """Inserts new gender"""
    try:
        new_gender = EmployeeGenderModel(**gender.model_dump())
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


def insert_nationality(nacionality: EmployeeNationalityTotvsSchema) -> None:
    """Inserts new nacionality"""
    try:
        new_nationality = EmployeeNationalityModel(**nacionality.model_dump())
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


def insert_cost_center(cost_center: CostCenterTotvsSchema) -> None:
    """Inserts new cost center"""
    try:
        new_cost_center = CostCenterModel(**cost_center.model_dump())
        db_session = get_db_session()
        if not db_session:
            logger.warning("No db session.")
            return

        logger.info("New: %s", str(new_cost_center))
        db_session.add(new_cost_center)
        db_session.commit()
    except IntegrityError as err:
        logger.warning("Error: %s", err.args[0])

    if db_session:
        db_session.close()


def insert_asset_type(asset_type: AssetTypeTotvsSchema) -> None:
    """Inserts new asset type"""
    try:
        new_asset_type = AssetTypeModel(**asset_type.model_dump())
        db_session = get_db_session()
        if not db_session:
            logger.warning("No db session.")
            return

        logger.info("New: %s", str(new_asset_type))
        db_session.add(new_asset_type)
        db_session.commit()
    except IntegrityError as err:
        logger.warning("Error: %s", err.args[0])

    if db_session:
        db_session.close()


def insert_asset(asset: AssetTotvsSchema) -> None:
    """Inserts new asset"""
    try:
        new_asset = AssetModel(**asset.model_dump())
        db_session = get_db_session()
        if not db_session:
            logger.warning("No db session.")
            return

        logger.info("New: %s", str(new_asset))
        db_session.add(new_asset)
        db_session.commit()
    except IntegrityError as err:
        logger.warning("Error: %s", err.args[0])

    if db_session:
        db_session.close()


def insert_role(role: EmployeeRoleTotvsSchema) -> None:
    """Inserts new role"""
    try:
        new_role = EmployeeRoleModel(**role.model_dump())
        db_session = get_db_session()
        if not db_session:
            logger.warning("No db session.")
            return

        logger.info("New: %s", str(new_role))
        db_session.add(new_role)
        db_session.commit()
    except IntegrityError as err:
        logger.warning("Error: %s", err.args[0])

    if db_session:
        db_session.close()
