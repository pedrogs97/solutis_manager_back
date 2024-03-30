"""Methods to access database"""

import json
import logging
from datetime import date, datetime
from typing import List, Type, Union

from pydantic_core import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from src.asset.models import AssetModel, AssetStatusModel, AssetTypeModel
from src.backends import get_db_session
from src.datasync.models import (
    AssetTypeTOTVSModel,
    EmployeeEducationalLevelTOTVSModel,
    EmployeeGenderTOTVSModel,
    EmployeeMaritalStatusTOTVSModel,
    EmployeeNationalityTOTVSModel,
    EmployeeRoleTOTVSModel,
    SyncModel,
)
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
from src.invoice.models import InvoiceModel
from src.people.models import EmployeeModel

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
    EMAIL, CARGO, SITUACAO, ADMISSAO, MATRICULA, ESCOLARIDADE
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
            national_identification=(
                row["CARTIDENTIDADE"] if row["CARTIDENTIDADE"] is not None else ""
            ),
            marital_status=row["CIVIL"] if row["CIVIL"] is not None else "",
            nationality=(
                row["NACIONALIDADE"] if row["NACIONALIDADE"] is not None else ""
            ),
            role=row["CARGO"] if row["CARGO"] is not None else "",
            status=row["SITUACAO"] if row["SITUACAO"] is not None else "",
            address=address,
            cell_phone=row["TELEFONE1"] if row["TELEFONE1"] is not None else "",
            email=row["EMAIL"] if row["EMAIL"] is not None else "",
            gender=row["SEXO"] if row["SEXO"] is not None else "",
            admission_date=(
                admission_datetime.date() if admission_datetime is not None else None
            ),
            registration=row["MATRICULA"] if row["MATRICULA"] else "",
            educational_level=row["ESCOLARIDADE"] if row["ESCOLARIDADE"] else "",
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
            code=(
                str(row["IDGRUPOPATRIMONIO"])
                if row["IDGRUPOPATRIMONIO"] is not None
                else ""
            ),
            group_code=(
                row["CODGRUPOPATRIMONIO"]
                if row["CODGRUPOPATRIMONIO"] is not None
                else ""
            ),
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
    PADRAOEQUIP, GARANTIA, LINHA, FORNECEDOR, NOTA, DEPRECIACAO
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
            invoice_number=row["NOTA"] if row["NOTA"] is not None else "",
            assurance_date=assurance_date,
            observations=row["OBSERVACOES"] if row["OBSERVACOES"] is not None else "",
            pattern=row["PADRAOEQUIP"] if row["PADRAOEQUIP"] is not None else "",
            operational_system=(
                row["SISTEMAOPERACIONAL"]
                if row["SISTEMAOPERACIONAL"] is not None
                else ""
            ),
            serial_number=row["SERIE"] if row["SERIE"] is not None else "",
            imei=row["IMEI"] if row["IMEI"] is not None else "",
            acquisition_date=acquisition_date,
            value=(
                float(str(row["VALORBASE"]).replace(",", "."))
                if row["VALORBASE"] is not None
                else 0.0
            ),
            ms_office=row["PACOTEOFFICE"] == "SIM",
            line_number=row["LINHA"] if row["LINHA"] is not None else "",
            operator=row["OPERADORA"] if row["OPERADORA"] is not None else "",
            accessories=row["ACESSORIOS"] if row["ACESSORIOS"] is not None else "",
            quantity=int(row["QUANTIDADE"]) if row["QUANTIDADE"] is not None else 0,
            unit=row["UNIDADE"] if row["UNIDADE"] is not None else "",
            active=row["ATIVO"] is not None and row["ATIVO"] == 1,
            depreciation=(
                float(str(row["DEPRECIACAO"]).replace(",", "."))
                if row["DEPRECIACAO"] is not None
                else 0.0
            ),
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
    db_session = get_db_session()
    if not db_session:
        logger.warning("No db session")
        return False
    asset_db = db_session.query(model_type).filter_by(code=totvs_schema.code).first()

    if not asset_db:
        db_session.close()
        return True
    checksum_from_totvs = get_checksum(totvs_schema)
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
            for key, value in schema_dict.items():
                if key != identifier:
                    setattr(current_info, key, value)
            db_session.add(current_info)
            db_session.commit()
        else:
            logger.info("New: %s", str(new_info))
            db_session.add(new_info)
            db_session.commit()
    except IntegrityError as err:
        logger.warning("Error: %s", err.args[0])
    except Exception as err:
        logger.error("Error: %s", err.args[0])
    finally:
        db_session.close()


def update_employee_totvs(totvs_employees: List[EmployeeTotvsSchema]):
    """Updates employees from totvs"""
    db_session = get_db_session()
    updates: List[EmployeeModel] = []
    try:
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

            role = (
                db_session.query(EmployeeRoleTOTVSModel)
                .filter(EmployeeRoleTOTVSModel.name == totvs_employee.role)
                .first()
            )

            nationality = (
                db_session.query(EmployeeNationalityTOTVSModel)
                .filter(
                    EmployeeNationalityTOTVSModel.description
                    == totvs_employee.nationality
                )
                .first()
            )

            marital_status = (
                db_session.query(EmployeeMaritalStatusTOTVSModel)
                .filter(
                    EmployeeMaritalStatusTOTVSModel.description
                    == totvs_employee.marital_status
                )
                .first()
            )
            gender = (
                db_session.query(EmployeeGenderTOTVSModel)
                .filter(EmployeeGenderTOTVSModel.description == totvs_employee.gender)
                .first()
            )

            if not gender:
                gender = (
                    db_session.query(EmployeeGenderTOTVSModel)
                    .filter(EmployeeGenderTOTVSModel.code == "M")
                    .first()
                )

            educational_level = (
                db_session.query(EmployeeEducationalLevelTOTVSModel)
                .filter(
                    EmployeeEducationalLevelTOTVSModel.description
                    == totvs_employee.educational_level
                )
                .first()
            )

            dict_employee = {
                **totvs_employee.model_dump(
                    exclude={
                        "role",
                        "nationality",
                        "marital_status",
                        "gender",
                        "educational_level",
                    }
                ),
                "role_id": role.id if role else None,
                "nationality_id": nationality.id if nationality else None,
                "marital_status_id": marital_status.id if marital_status else None,
                "gender_id": gender.id,
                "educational_level_id": (
                    educational_level.id if educational_level else None
                ),
            }

            exist = None
            for update in updates:
                if (
                    update.code == dict_employee["code"]
                    or update.taxpayer_identification
                    == dict_employee["taxpayer_identification"]
                ):
                    exist = update
                    break
            if exist:
                updates.remove(exist)

            if employee_db:
                for key, value in dict_employee.items():
                    if key not in ("code", "taxpayer_identification"):
                        setattr(employee_db, key, value)
                updates.append(employee_db)
            else:
                update_employee = EmployeeModel(**dict_employee)
                updates.append(update_employee)

        db_session.add_all(updates)
        db_session.commit()
        logger.info("Update Employee from TOTVS. Total=%s", str(len(updates)))
    except Exception as err:
        logger.error("Error: %s", err.args[0])
    db_session.close()


def update_invoice_number(
    invoice_number: str, asset: AssetModel, db_session
) -> InvoiceModel:
    """Updates asset invoice"""
    asset_invoice_db = (
        db_session.query(InvoiceModel)
        .filter(InvoiceModel.number == invoice_number)
        .first()
    )

    if not asset_invoice_db:
        asset_invoice_new = InvoiceModel(number=invoice_number)
        asset_invoice_new.assets.append(asset)
        db_session.add(asset_invoice_new)
        db_session.commit()
    elif asset_invoice_db.asset.code != asset.code:
        asset_invoice_db.asset = asset
        db_session.add(asset_invoice_db)
        db_session.commit()


def update_asset_totvs(totvs_assets: List[AssetTotvsSchema]):
    """Updates assets from totvs"""
    db_session = get_db_session()
    updates: List[AssetModel] = []
    try:
        for totvs_asset in totvs_assets:
            asset_db = (
                db_session.query(AssetModel)
                .filter(AssetModel.code == totvs_asset.code)
                .first()
            )

            dict_totvs_asset = totvs_asset.model_dump(
                exclude={
                    "type",
                    "cost_center",
                    "invoice_number",
                }
            )

            asset_description_splited = totvs_asset.description.split(" ")
            if len(asset_description_splited) > 1:
                asset_simple_description = asset_description_splited[0]
                asset_description = (
                    asset_simple_description + " " + asset_description_splited[1]
                )

                if asset_simple_description.startswith(
                    ("CADEIRA", "MESA", "ARMARIO", "GAVETEIRO", "ROUPEIRO", "SOFA")
                ):
                    asset_simple_description = "MOBILIÁRIO"

                if asset_simple_description.startswith(("CELULAR")):
                    asset_simple_description = "TELEFONIA"

                asset_type = (
                    db_session.query(AssetTypeModel)
                    .filter(
                        or_(
                            AssetTypeModel.name.like(asset_simple_description),
                            AssetTypeModel.name.like(asset_description),
                        )
                    )
                    .first()
                )
            else:
                asset_simple_description = asset_description_splited[0]
                asset_type = (
                    db_session.query(AssetTypeModel)
                    .filter(AssetTypeModel.name.like(asset_simple_description))
                    .first()
                )

            asset_group = (
                db_session.query(AssetTypeTOTVSModel)
                .filter(AssetTypeTOTVSModel.name == totvs_asset.type)
                .first()
            )

            status = 1 if totvs_asset.active else 6
            asset_status = (
                db_session.query(AssetStatusModel)
                .filter(AssetStatusModel.id == status)
                .first()
            )

            asset_invoice = None
            if totvs_asset.invoice_number:
                asset_invoice = (
                    db_session.query(InvoiceModel)
                    .filter(InvoiceModel.number == totvs_asset.invoice_number)
                    .first()
                )

                if not asset_invoice:
                    asset_invoice = InvoiceModel(number=totvs_asset.invoice_number)

            dict_asset = {
                **dict_totvs_asset,
                "asset_group_id": asset_group.id if asset_group else None,
                "type": asset_type,
                "status": asset_status,
                "invoice": asset_invoice,
            }

            exist_index = 0
            for index, update in enumerate(updates):
                if update.code == dict_asset["code"]:
                    exist_index = index
                    break
            if exist_index:
                updates.pop(exist_index)

            if asset_db:
                for key, value in dict_asset.items():
                    if key != "code":
                        setattr(asset_db, key, value)

                updates.append(asset_db)
            else:
                new_asset = AssetModel(**dict_asset)
                updates.append(new_asset)

        db_session.add_all(updates)
        db_session.commit()
        db_session.flush()
        logger.info("Update Assets from TOTVS. Total=%s", str(len(updates)))
    except Exception as err:
        logger.error("Error: %s", err.args[0])
    db_session.close()
