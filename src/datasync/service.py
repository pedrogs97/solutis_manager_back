"""Methods to access database"""
import json
import logging
from datetime import date, datetime
from typing import Union

from pydantic_core import ValidationError
from sqlalchemy.exc import IntegrityError

from src.backends import get_db_session
from src.datasync.models import SyncModel
from src.datasync.schemas import (
    AssetTotvsSchema,
    AssetTypeTotvsSchema,
    BaseTotvsSchema,
    CostCenterTotvsSchema,
    EmployeeGenderTotvsSchema,
    EmployeeMatrialStatusTotvsSchema,
    EmployeeNationalityTotvsSchema,
    EmployeeRoleTotvsSchema,
    EmployeeTotvsSchema,
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
    finally:
        db_session.close()


def totvs_to_employee_schema(
    row,
) -> Union[EmployeeTotvsSchema, None]:
    """Convert data from TOTVS to EmployeeTotvsSchema

    From
    CODIGO, NOME, DTNASCIMENTO, CIVIL, SEXO , NACIONALIDADE, RUA,
    NUMERO, COMPLEMENTO, BAIRRO, ESTADO, CIDADE, CEP, PAIS, CPF,
    TELEFONE1, CARTIDENTIDADE, UFCARTIDENT, ORGEMISSORIDENT, DTEMISSAOIDENT,
    EMAIL, CARGO
    """
    try:
        address = f"{row['RUA']}, {row['NUMERO']}, {row['COMPLEMENTO']}, {row['BAIRRO']}. \
            {row['CIDADE']} - {row['ESTADO']}, {row['PAIS']}. {row['CEP']}"
        birthday_datetime: datetime = row["DTNASCIMENTO"]
        return EmployeeTotvsSchema(
            code=str(row["CODIGO"]) if row["CODIGO"] is not None else "",
            full_name=row["NOME"] if row["NOME"] is not None else "",
            birthday=birthday_datetime.date(),
            taxpayer_identification=row["CPF"] if row["CPF"] is not None else "",
            nacional_identification=row["CARTIDENTIDADE"]
            if row["CARTIDENTIDADE"] is not None
            else "",
            marital_status=row["CIVIL"] if row["CIVIL"] is not None else "",
            nationality=row["NACIONALIDADE"]
            if row["NACIONALIDADE"] is not None
            else "",
            role=row["CARGO"] if row["CARGO"] is not None else "",
            address=address,
            cell_phone=row["TELEFONE1"] if row["TELEFONE1"] is not None else "",
            email=row["EMAIL"] if row["EMAIL"] is not None else "",
            gender=row["SEXO"] if row["SEXO"] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_marital_status_schema(
    row,
) -> Union[EmployeeMatrialStatusTotvsSchema, None]:
    """Convert data from TOTVS to EmployeeMatrialStatusTotvsSchema

    From
    DESCRICAO, CODINTERNO
    """
    try:
        return EmployeeMatrialStatusTotvsSchema(
            code=row["CODINTERNO"] if row["CODINTERNO"] is not None else "",
            description=row["DESCRICAO"] if row["DESCRICAO"] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_gender_schema(
    row,
) -> Union[EmployeeGenderTotvsSchema, None]:
    """Convert data from TOTVS to EmployeeGenderTotvsSchema

    From
    DESCRICAO, CODINTERNO
    """
    try:
        return EmployeeGenderTotvsSchema(
            code=row["CODINTERNO"] if row["CODINTERNO"] is not None else "",
            description=row["DESCRICAO"] if row["DESCRICAO"] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_nationality_schema(
    row,
) -> Union[EmployeeNationalityTotvsSchema, None]:
    """Convert data from TOTVS to EmployeeNationalityTotvsSchema

    From
    DESCRICAO, CODINTERNO
    """
    try:
        return EmployeeNationalityTotvsSchema(
            code=row["CODINTERNO"] if row["CODINTERNO"] is not None else "",
            description=row["DESCRICAO"] if row["DESCRICAO"] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_cost_center_schema(
    row,
) -> Union[CostCenterTotvsSchema, None]:
    """Convert data from TOTVS to CostCenterTotvsSchema

    From
    CODREDUZIDO, NOME, DESCRICAO
    """
    try:
        return CostCenterTotvsSchema(
            code=row["CODREDUZIDO"] if row["CODREDUZIDO"] is not None else "",
            name=row["NOME"] if row["NOME"] is not None else "",
            classification=row["DESCRICAO"] if row["DESCRICAO"] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_asset_type_schema(
    row,
) -> Union[AssetTypeTotvsSchema, None]:
    """Convert data from TOTVS to AssetTypeTotvsSchema

    From
    IDGRUPOPATRIMONIO, CODGRUPOPATRIMONIO, DESCRICAO
    """
    try:
        return AssetTypeTotvsSchema(
            code=str(row["IDGRUPOPATRIMONIO"])
            if row["IDGRUPOPATRIMONIO"] is not None
            else "",
            group_code=row["CODGRUPOPATRIMONIO"]
            if row["CODGRUPOPATRIMONIO"] is not None
            else "",
            name=row["DESCRICAO"] if row["DESCRICAO"] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_asset_schema(
    row,
) -> Union[AssetTotvsSchema, None]:
    """Convert data from TOTVS to AssetTotvsSchema

    From
    IDPATRIMONIO, DESCRICAO, TIPO,
    ATIVO, DATAAQUISICAO, PATRIMONIO, QUANTIDADE, UNIDADE, OBSERVACOES,
    CODIGOBARRA, CENTROCUSTO, VALORBASE, VRDEPACUCORRIGIDA, SERIE,
    IMEI, ACESSORIOS, OPERADORA, SISTEMAOPERACIONAL, PACOTEOFFICE,
    PADRAOEQUIP, GARANTIA, LINHA, FORNECEDOR
    """
    try:
        acquisition_date: datetime = row["DATAAQUISICAO"]
        assurance_date: datetime = row["GARANTIA"]

        return AssetTotvsSchema(
            code=str(row["IDPATRIMONIO"]) if row["IDPATRIMONIO"] is not None else "",
            type=row["TIPO"] if row["TIPO"] is not None else "",
            cost_center=row["CENTROCUSTO"] if row["CENTROCUSTO"] is not None else "",
            register_number=row["PATRIMONIO"] if row["PATRIMONIO"] is not None else "",
            description=row["DESCRICAO"] if row["DESCRICAO"] is not None else "",
            supplier=row["FORNECEDOR"] if row["FORNECEDOR"] is not None else "",
            assurance_date=assurance_date,
            observations=row["OBSERVACOES"] if row["OBSERVACOES"] is not None else "",
            pattern=row["PADRAOEQUIP"] if row["PADRAOEQUIP"] is not None else "",
            operational_system=row["SISTEMAOPERACIONAL"]
            if row["SISTEMAOPERACIONAL"] is not None
            else "",
            serial_number=row["SERIE"] if row["SERIE"] is not None else "",
            imei=row["IMEI"] if row["IMEI"] is not None else "",
            acquisition_date=acquisition_date,
            value=float(str(row["VALORBASE"]).replace(",", "."))
            if row["VALORBASE"] is not None
            else 0.0,
            ms_office=row["PACOTEOFFICE"] == "SIM",
            line_number=row["LINHA"] if row["LINHA"] is not None else "",
            operator=row["OPERADORA"] if row["OPERADORA"] is not None else "",
            accessories=row["ACESSORIOS"] if row["ACESSORIOS"] is not None else "",
            quantity=int(row["QUANTIDADE"]) if row["QUANTIDADE"] is not None else 0,
            unit=row["UNIDADE"] if row["UNIDADE"] is not None else "",
            active=row["ATIVO"] is not None and row["ATIVO"] == 1,
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_role_schema(
    row,
) -> Union[EmployeeRoleTotvsSchema, None]:
    """Convert data from TOTVS to EmployeeRoleTotvsSchema

    From
    CODIGO, NOME
    """
    try:
        return EmployeeRoleTotvsSchema(
            code=row["CODIGO"] if row["CODIGO"] is not None else "",
            name=row["NOME"] if row["NOME"] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def default_obj(obj):
    """Return default value for an object. Used to parse object to string"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return str(obj)


def get_checksum(schema: BaseTotvsSchema) -> bytes:
    """Returns a schema as bytes"""
    return json.dumps(
        schema.model_dump(), sort_keys=True, indent=2, default=default_obj
    ).encode("utf-8")


def verify_changes(
    totvs_schema: BaseTotvsSchema, db_schema: BaseTotvsSchema, model_type
) -> bool:
    """
    Check if the TotvsSchema object is different from the TotvsSchema in the database.
    Returns True if it does not exist in the database.
    """
    checksum_from_totvs = get_checksum(totvs_schema)
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    asset_db = db_session.query(model_type).filter_by(code=totvs_schema.code).first()

    if not asset_db:
        db_session.close()
        return True
    db_dict = {**asset_db.__dict__}
    db_dict.pop("_sa_instance_state")
    db_dict.pop("id")
    checksum_from_db = get_checksum(db_schema(**db_dict))
    db_session.close()
    return checksum_from_db != checksum_from_totvs


def insert(schema: BaseTotvsSchema, model_type) -> None:
    """Insert new or change"""
    db_session = get_db_session()
    try:
        new_info = model_type(**schema.model_dump())
        if not db_session:
            logger.warning("No db session.")
            return

        current_info = (
            db_session.query(model_type).filter(model_type.code == schema.code).first()
        )

        if current_info:
            logger.info("Update: %s", str(new_info))
            db_session.delete(current_info)
            db_session.commit()
            db_session.add(new_info)
            db_session.commit()
        else:
            logger.info("New: %s", str(new_info))
            db_session.add(new_info)
            db_session.commit()
    except IntegrityError as err:
        logger.warning("Error: %s", err.args[0])
    finally:
        db_session.close()
