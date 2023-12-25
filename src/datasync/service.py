"""Methods to access database"""
import json
import logging
from datetime import date, datetime
from typing import List, Type, Union

from pydantic_core import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from src.asset.models import AssetModel, AssetTypeModel
from src.backends import get_db_session
from src.datasync.models import SyncModel
from src.datasync.schemas import (
    AssetTotvsSchema,
    AssetTypeTotvsSchema,
    BaseTotvsSchema,
    CostCenterTotvsSchema,
    EmployeeEducationalLevelTotvsSchema,
    EmployeeGenderTotvsSchema,
    EmployeeMaritalStatusTotvsSchema,
    EmployeeNationalityTotvsSchema,
    EmployeeRoleTotvsSchema,
    EmployeeTotvsSchema,
)
from src.people.models import (
    CostCenterModel,
    EmployeeGenderModel,
    EmployeeMaritalStatusModel,
    EmployeeModel,
    EmployeeNationalityModel,
    EmployeeRoleModel,
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
    EMAIL, CARGO, SITUACAO, ADMISSAO, MATRICULA
    """
    try:
        city = str(row["CIDADE"]).strip()
        cep = str(row["CEP"]).strip()
        street = str(row["RUA"]).strip()
        num = str(row["NUMERO"]).strip() if row["NUMERO"] else ""
        comp = str(row["COMPLEMENTO"]).strip() if row["COMPLEMENTO"] else ""
        neighborhood = str(row["BAIRRO"]).strip() if row["COMPLEMENTO"] else ""
        state = str(row["ESTADO"]).strip()
        country = str(row["PAIS"]).strip().replace(":", "").replace(".", "")

        address = f"{street};{num};{comp};{neighborhood};{city};{state};{country};{cep}"
        birthday_datetime: datetime = row["DTNASCIMENTO"]
        admission_datetime: datetime = row["ADMISSAO"]
        return EmployeeTotvsSchema(
            code=str(row["CODIGO"]) if row["CODIGO"] is not None else "",
            full_name=row["NOME"] if row["NOME"] is not None else "",
            birthday=birthday_datetime.date(),
            taxpayer_identification=row["CPF"] if row["CPF"] is not None else "",
            national_identification=row["CARTIDENTIDADE"]
            if row["CARTIDENTIDADE"] is not None
            else "",
            marital_status=row["CIVIL"] if row["CIVIL"] is not None else "",
            nationality=row["NACIONALIDADE"]
            if row["NACIONALIDADE"] is not None
            else "",
            role=row["CARGO"] if row["CARGO"] is not None else "",
            status=row["SITUACAO"] if row["SITUACAO"] is not None else "",
            address=address,
            cell_phone=row["TELEFONE1"] if row["TELEFONE1"] is not None else "",
            email=row["EMAIL"] if row["EMAIL"] is not None else "",
            gender=row["SEXO"] if row["SEXO"] is not None else "",
            admission_date=admission_datetime.date(),
            registration=row["MATRICULA"] if row["MATRICULA"] else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_educational_level_schema(
    row,
) -> Union[EmployeeEducationalLevelTotvsSchema, None]:
    """Convert data from TOTVS to EmployeeEducationalLevelTotvsSchema

    From
    DESCRICAO, CODINTERNO
    """
    try:
        return EmployeeEducationalLevelTotvsSchema(
            code=row["CODINTERNO"] if row["CODINTERNO"] is not None else "",
            description=row["DESCRICAO"] if row["DESCRICAO"] is not None else "",
        )
    except ValidationError as err:
        error_msg = f"Field: {err.args[0]} Message: {err.args[1]}"
        logger.warning("Error: Field: %s", error_msg)
        return None


def totvs_to_marital_status_schema(
    row,
) -> Union[EmployeeMaritalStatusTotvsSchema, None]:
    """Convert data from TOTVS to EmployeeMaritalStatusTotvsSchema

    From
    DESCRICAO, CODINTERNO
    """
    try:
        return EmployeeMaritalStatusTotvsSchema(
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


def insert(schema: BaseTotvsSchema, model_type: Type, identifier="code") -> None:
    """Insert new or change"""
    db_session = get_db_session()
    try:
        schema_dict = schema.model_dump()
        new_info = model_type(**schema_dict)
        if not db_session:
            logger.warning("No db session.")
            return
        query = db_session.query(model_type)
        if identifier == "code":
            query = query.filter(model_type.code == schema.code)
        else:
            query = query.filter(
                or_(
                    model_type.code == schema.code,
                    getattr(model_type, identifier) == schema_dict[identifier],
                )
            )
        current_info = query.first()
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


def update_employee_totvs(totvs_employees: List[EmployeeTotvsSchema]):
    """Updates employees from totvs"""
    db_session = get_db_session()
    updates: List[EmployeeModel] = []
    for totvs_employee in totvs_employees:
        employee_db = (
            db_session.query(EmployeeModel)
            .filter(
                or_(
                    EmployeeModel.code == totvs_employee.code,
                    EmployeeModel.taxpayer_identification
                    == totvs_employee.taxpayer_identification,
                )
            )
            .first()
        )
        if employee_db:
            db_session.delete(employee_db)
            db_session.commit()

        role = (
            db_session.query(EmployeeRoleModel)
            .filter(EmployeeRoleModel.name == totvs_employee.role)
            .first()
        )
        nationality = (
            db_session.query(EmployeeNationalityModel)
            .filter(EmployeeNationalityModel.description == totvs_employee.nationality)
            .first()
        )
        marital_status = (
            db_session.query(EmployeeMaritalStatusModel)
            .filter(
                EmployeeMaritalStatusModel.description == totvs_employee.marital_status
            )
            .first()
        )
        gender = (
            db_session.query(EmployeeGenderModel)
            .filter(EmployeeGenderModel.description == totvs_employee.gender)
            .first()
        )

        dict_employee = {
            **totvs_employee.model_dump(
                exclude={"role", "nationality", "marital_status", "gender"}
            ),
            "role": role,
            "nationality": nationality,
            "marital_status": marital_status,
            "gender": gender,
        }
        update_employee = EmployeeModel(**dict_employee)
        exist = None
        for update in updates:
            if (
                update.code == update_employee.code
                or update.taxpayer_identification
                == update_employee.taxpayer_identification
            ):
                exist = update
                break
        if exist:
            updates.remove(exist)
        updates.append(update_employee)

    db_session.add_all(updates)
    db_session.commit()
    logger.info("Update Employee from TOTVS. Total=%s", str(len(updates)))
    db_session.close()


def update_marital_status_totvs(
    totvs_marital_status: List[EmployeeMaritalStatusTotvsSchema],
):
    """Updates marital_status from totvs"""
    db_session = get_db_session()
    updates: List[EmployeeMaritalStatusModel] = []
    for totvs_marital_status_item in totvs_marital_status:
        db_marital_status = (
            db_session.query(EmployeeMaritalStatusModel)
            .filter(EmployeeMaritalStatusModel.code == totvs_marital_status_item.code)
            .first()
        )
        if db_marital_status:
            db_marital_status.description = totvs_marital_status_item.description
            updates.append(db_marital_status)
            continue

        updates.append(
            EmployeeMaritalStatusModel(**totvs_marital_status_item.model_dump())
        )

    db_session.add_all(updates)
    db_session.commit()

    logger.info("Update Matrimonial Status from TOTVS. Total=%s", str(len(updates)))
    db_session.close()


def update_gender_totvs(
    totvs_gender: List[EmployeeGenderTotvsSchema],
):
    """Updates gender from totvs"""
    db_session = get_db_session()
    updates: List[EmployeeGenderModel] = []
    for totvs_gender_item in totvs_gender:
        db_gender = (
            db_session.query(EmployeeGenderModel)
            .filter(EmployeeGenderModel.code == totvs_gender_item.code)
            .first()
        )
        if db_gender:
            db_gender.description = totvs_gender_item.description
            updates.append(db_gender)
            continue

        updates.append(EmployeeGenderModel(**totvs_gender_item.model_dump()))

    db_session.add_all(updates)
    db_session.commit()
    logger.info("Update Gender from TOTVS. Total=%s", str(len(updates)))
    db_session.close()


def update_nationality_totvs(
    totvs_nationality: List[EmployeeNationalityTotvsSchema],
):
    """Updates nationality from totvs"""
    db_session = get_db_session()
    updates: List[EmployeeNationalityModel] = []
    for totvs_nationality_item in totvs_nationality:
        db_nationality = (
            db_session.query(EmployeeNationalityModel)
            .filter(EmployeeNationalityModel.code == totvs_nationality_item.code)
            .first()
        )
        if db_nationality:
            db_nationality.description = totvs_nationality_item.description
            updates.append(db_nationality)
            continue

        updates.append(EmployeeNationalityModel(**totvs_nationality_item.model_dump()))

    db_session.add_all(updates)
    db_session.commit()
    logger.info("Update Nationality from TOTVS. Total=%s", str(len(updates)))
    db_session.close()


def update_role_totvs(
    totvs_role: List[EmployeeRoleTotvsSchema],
):
    """Updates role from totvs"""
    db_session = get_db_session()
    updates: List[EmployeeRoleModel] = []
    for totvs_role_item in totvs_role:
        db_role = (
            db_session.query(EmployeeRoleModel)
            .filter(EmployeeRoleModel.code == totvs_role_item.code)
            .first()
        )
        if db_role:
            db_role.name = totvs_role_item.name
            updates.append(db_role)
            continue

        updates.append(EmployeeRoleModel(**totvs_role_item.model_dump()))

    db_session.add_all(updates)
    db_session.commit()
    logger.info("Update Role from TOTVS. Total=%s", str(len(updates)))
    db_session.close()


def update_asset_totvs(totvs_assets: List[AssetTotvsSchema]):
    """Updates assets from totvs"""
    db_session = get_db_session()
    updates: List[AssetModel] = []
    for totvs_asset in totvs_assets:
        asset_db = (
            db_session.query(AssetModel)
            .filter(AssetModel.code == totvs_asset.code)
            .first()
        )
        if asset_db:
            db_session.delete(asset_db)
            db_session.commit()

        asset_type = (
            db_session.query(AssetTypeModel)
            .filter(AssetTypeModel.name == totvs_asset.type)
            .first()
        )

        if not asset_type:
            continue

        dict_asset = {
            **totvs_asset.model_dump(exclude={"asset_type", "cost_center"}),
            "type": asset_type,
        }

        update_asset = AssetModel(**dict_asset)
        exist = None
        for update in updates:
            if update.code == update_asset.code:
                exist = update
                break
        if exist:
            updates.remove(exist)
        updates.append(update_asset)

    db_session.add_all(updates)
    db_session.commit()
    logger.info("Update Assets from TOTVS. Total=%s", str(len(updates)))
    db_session.close()


def update_asset_type_totvs(
    totvs_asset_type: List[AssetTypeTotvsSchema],
):
    """Updates asset type from totvs"""
    db_session = get_db_session()
    updates: List[AssetTypeModel] = []
    for totvs_asset_type_item in totvs_asset_type:
        db_asset_type = (
            db_session.query(AssetTypeModel)
            .filter(AssetTypeModel.code == totvs_asset_type_item.code)
            .first()
        )
        if db_asset_type:
            db_asset_type.group_code = totvs_asset_type_item.group_code
            db_asset_type.name = totvs_asset_type_item.name
            updates.append(db_asset_type)
            continue

        updates.append(
            AssetTypeModel(
                **totvs_asset_type_item.model_dump(),
                acronym=totvs_asset_type_item.name[:3].upper(),
            )
        )

    db_session.add_all(updates)
    db_session.commit()
    logger.info("Update Asset Types from TOTVS. Total=%s", str(len(updates)))
    db_session.close()


def update_cost_center_totvs(
    totvs_cost_center: List[CostCenterTotvsSchema],
):
    """Updates asset type from totvs"""
    db_session = get_db_session()
    updates: List[CostCenterModel] = []
    for totvs_cost_center_item in totvs_cost_center:
        db_cost_center = (
            db_session.query(CostCenterModel)
            .filter(CostCenterModel.code == totvs_cost_center_item.code)
            .first()
        )
        if db_cost_center:
            db_cost_center.code = totvs_cost_center_item.code
            db_cost_center.classification = totvs_cost_center_item.classification
            db_cost_center.name = totvs_cost_center_item.name
            updates.append(db_cost_center)
            continue

        updates.append(CostCenterModel(**totvs_cost_center_item.model_dump()))

    db_session.add_all(updates)
    db_session.commit()
    logger.info("Update Cost Centers from TOTVS. Total=%s", str(len(updates)))
    db_session.close()
