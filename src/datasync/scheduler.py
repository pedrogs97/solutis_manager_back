"""Scheduler Service"""

import logging
from time import time
from typing import List

from src.database import ExternalDatabase
from src.datasync.models import (
    AssetTOTVSModel,
    AssetTypeTOTVSModel,
    CostCenterTOTVSModel,
    EmployeeEducationalLevelTOTVSModel,
    EmployeeGenderTOTVSModel,
    EmployeeMaritalStatusTOTVSModel,
    EmployeeNationalityTOTVSModel,
    EmployeeRoleTOTVSModel,
    EmployeeTOTVSModel,
)
from src.datasync.schemas import (
    AssetTotvsSchema,
    AssetTypeTotvsSchema,
    CostCenterTotvsSchema,
    EmployeeEducationalLevelTotvsSchema,
    EmployeeGenderTotvsSchema,
    EmployeeMaritalStatusTotvsSchema,
    EmployeeNationalityTotvsSchema,
    EmployeeRoleTotvsSchema,
    EmployeeTotvsSchema,
)
from src.datasync.service import (
    insert,
    set_last_sync,
    totvs_to_asset_schema,
    totvs_to_asset_type_schema,
    totvs_to_cost_center_schema,
    totvs_to_educational_level_schema,
    totvs_to_employee_schema,
    totvs_to_gender_schema,
    totvs_to_marital_status_schema,
    totvs_to_nationality_schema,
    totvs_to_role_schema,
    update_asset_totvs,
    update_employee_totvs,
    verify_changes,
)

logger = logging.getLogger(__name__)


class SchedulerService:
    """Scheduler Service class"""

    TIME_INFO = "Execution time: %s ms"

    SQL_PPESSOA = """SELECT
	p.CODIGO, p.NOME, p.DTNASCIMENTO, c.DESCRICAO AS CIVIL, s.DESCRICAO AS SEXO,
    n.DESCRICAO AS NACIONALIDADE, p.RUA, p.NUMERO, p.COMPLEMENTO, p.BAIRRO,
    p.ESTADO, p.CIDADE, p.CEP, p.PAIS, p.CPF, p.TELEFONE1, p.CARTIDENTIDADE,
    p.UFCARTIDENT, p.ORGEMISSORIDENT, p.DTEMISSAOIDENT, p.EMAIL, pf.NOME AS CARGO,
    cs.DESCRICAO as SITUACAO, f.DATAADMISSAO AS ADMISSAO, f.CHAPA AS MATRICULA, i.DESCRICAO as ESCOLARIDADE
    FROM [SINESTRO].[CorporeRM].[dbo].[PPESSOA] as p
    LEFT JOIN [SINESTRO].[CorporeRM].[dbo].[PCODESTCIVIL] AS c
    ON p.ESTADOCIVIL = c.CODINTERNO
    LEFT JOIN [SINESTRO].[CorporeRM].[dbo].[PCODSEXO] AS s
    ON p.SEXO = s.CODINTERNO
    LEFT JOIN [SINESTRO].[CorporeRM].[dbo].[PCODNACAO] n
    ON n.CODINTERNO = p.NACIONALIDADE
    LEFT JOIN [SINESTRO].[CorporeRM].[dbo].[PFUNC] as f
    ON f.CODPESSOA = p.CODIGO
    LEFT JOIN [SINESTRO].[CorporeRM].[dbo].[PFUNCAO] as pf
    ON f.CODFUNCAO = pf.CODIGO
    LEFT JOIN [SINESTRO].[CorporeRM].[dbo].[PCODSITUACAO] as cs
    ON cs.CODCLIENTE = f.CODSITUACAO
    LEFT JOIN [SINESTRO].[CorporeRM].[dbo].[PCODINSTRUCAO] as i
    ON i.CODINTERNO = p.GRAUINSTRUCAO"""

    SQL_PCODESTCIVIL = """SELECT DESCRICAO, CODINTERNO FROM [SINESTRO].[CorporeRM].[dbo].[PCODESTCIVIL];"""

    SQL_PCODESEXO = (
        """SELECT DESCRICAO, CODINTERNO FROM [SINESTRO].[CorporeRM].[dbo].[PCODSEXO];"""
    )

    SQL_PCODNACAO = """SELECT DESCRICAO, CODINTERNO FROM [SINESTRO].[CorporeRM].[dbo].[PCODNACAO];"""

    SQL_GCCUSTO = """SELECT cc.CODREDUZIDO, cc.NOME, cls.DESCRICAO
    FROM [SINESTRO].[CorporeRM].[dbo].[GCCUSTO] cc
    LEFT JOIN CCLASSIFICACC AS cls
    ON cls.CODCLASSIFICA = cc.CODCLASSIFICA
    WHERE cc.CODCOLIGADA = 1;"""

    SQL_IPATRIMONIO = """SELECT p.IDPATRIMONIO, p.DESCRICAO, g.DESCRICAO AS TIPO,
    p.ATIVO, p.DATAAQUISICAO, p.PATRIMONIO, p.QUANTIDADE, p.UNIDADE, p.OBSERVACOES,
    p.CODIGOBARRA, c.NOME AS CENTROCUSTO, p.VALORBASE, p.VRDEPACUCORRIGIDA, pc.SERIE,
    pc.IMEI, pc.ACESSORIOS, pc.OPERADORA, pc.SISTEMAOPERACIONAL, pc.PACOTEOFFICE,
    pc.PADRAOEQUIP, ga.DATAEXPIRACAO AS GARANTIA, pc.MANUT5 AS LINHA,
    f.NOMEFANTASIA as FORNECEDOR, p.NUMERODOCUMENTO as NOTA, d.SALDORESIDUAL as DEPRECIACAO
    FROM CorporeRM_SI.dbo.IPATRIMONIO AS p
    LEFT JOIN [SINESTRO].[CorporeRM].[dbo].[IGRUPOPATRIMONIO] AS g
    ON g.IDGRUPOPATRIMONIO = p.IDGRUPOPATRIMONIO
    LEFT JOIN [SINESTRO].[CorporeRM].[dbo].[GCCUSTO] AS c
    ON P.CODCENTROCUSTO = c.CODCCUSTO
    LEFT JOIN [SINESTRO].[CorporeRM].[dbo].[IPATRIMONIOCOMPL] AS pc
    ON pc.IDPATRIMONIO = p.IDPATRIMONIO
    LEFT JOIN [SINESTRO].[CorporeRM].[dbo].[IGARANTIA] AS ga
    ON ga.IDPATRIMONIO = p.IDPATRIMONIO
    LEFT JOIN [SINESTRO].[CorporeRM].[dbo].[FCFO] as f
    ON f.CODCFO = p.CODFORNECEDOR
    LEFT JOIN
    (SELECT TOP 1 IDPATRIMONIO, SALDORESIDUAL
        FROM [SINESTRO].[CorporeRM].[dbo].[ISALDOCALCULOPATRIMONIOMOEDA]
        WHERE IDPATRIMONIO IN (SELECT IDPATRIMONIO FROM [SINESTRO].[CorporeRM].[dbo].[ISALDOCALCULOPATRIMONIOMOEDA] WHERE RECMODIFIEDON = (SELECT MAX(RECMODIFIEDON) FROM [SINESTRO].[CorporeRM].[dbo].[ISALDOCALCULOPATRIMONIOMOEDA]))
        ORDER BY IDPATRIMONIO DESC) as d
    ON d.IDPATRIMONIO = p.IDPATRIMONIO
    WHERE (p.CODCOLIGADA = 1)"""

    SQL_IGRUPOPATRIMONIO = """SELECT IDGRUPOPATRIMONIO, CODGRUPOPATRIMONIO, DESCRICAO
    FROM [SINESTRO].[CorporeRM].[dbo].[IGRUPOPATRIMONIO]
    WHERE CODCOLIGADA = 1"""

    SQL_PFUNCAO = """SELECT CODIGO, NOME
    FROM [SINESTRO].[CorporeRM].[dbo].[PFUNCAO]
    WHERE CODCOLIGADA = 1"""

    SQL_PCODINSTRUCAO = """
    SELECT CODINTERNO, DESCRICAO FROM [SINESTRO].[CorporeRM].[dbo].[PCODINSTRUCAO]"""

    def __init__(self, force=False) -> None:
        self._force = force

    def _get_employees_totvs(self):
        """Excute procedure to retrive TOVTS emplyoee data"""
        logger.info("Retrive employee from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_PPESSOA)
        rows = cursor.fetchall()
        cnxn = external_db.get_connection()
        cnxn.close()
        new_changes: List[EmployeeTotvsSchema] = []
        for row in rows:
            employee_totvs = totvs_to_employee_schema(row)
            if not employee_totvs:
                break
            if verify_changes(employee_totvs, EmployeeTotvsSchema, EmployeeTOTVSModel):
                new_changes.append(employee_totvs)
                insert(employee_totvs, EmployeeTOTVSModel, "taxpayer_identification")
        update_employee_totvs(new_changes)
        end = time()
        elapsed_time = end - start
        logger.info(self.TIME_INFO, str(elapsed_time))
        set_last_sync(len(new_changes), elapsed_time, "employee")
        logger.info("Retrive employee from TOTVS end.")

    def _get_educational_level_totvs(self):
        """Excute procedure to retrive TOVTS educational level data"""
        logger.info("Retrive educational level from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_PCODINSTRUCAO)
        rows = cursor.fetchall()
        cnxn = external_db.get_connection()
        cnxn.close()
        new_changes: List[EmployeeEducationalLevelTotvsSchema] = []
        for row in rows:
            educational_level_totvs = totvs_to_educational_level_schema(row)
            if not educational_level_totvs:
                break
            if verify_changes(
                educational_level_totvs,
                EmployeeEducationalLevelTotvsSchema,
                EmployeeEducationalLevelTOTVSModel,
            ):
                new_changes.append(educational_level_totvs)
                insert(educational_level_totvs, EmployeeEducationalLevelTOTVSModel)

        end = time()
        elapsed_time = end - start
        logger.info(self.TIME_INFO, str(elapsed_time))
        set_last_sync(len(new_changes), elapsed_time, "educational_level")
        logger.info("Retrive educational level from TOTVS end.")

    def _get_marital_status_totvs(self):
        """Excute procedure to retrive TOVTS marital status data"""
        logger.info("Retrive marital status from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_PCODESTCIVIL)
        rows = cursor.fetchall()
        cnxn = external_db.get_connection()
        cnxn.close()
        new_changes: List[EmployeeMaritalStatusTotvsSchema] = []
        for row in rows:
            marital_status_totvs = totvs_to_marital_status_schema(row)
            if not marital_status_totvs:
                break
            if verify_changes(
                marital_status_totvs,
                EmployeeMaritalStatusTotvsSchema,
                EmployeeMaritalStatusTOTVSModel,
            ):
                new_changes.append(marital_status_totvs)
                insert(marital_status_totvs, EmployeeMaritalStatusTOTVSModel)
        end = time()
        elapsed_time = end - start
        logger.info(self.TIME_INFO, str(elapsed_time))
        set_last_sync(len(new_changes), elapsed_time, "marital_status")
        logger.info("Retrive marital status from TOTVS end.")

    def _get_gender_totvs(self):
        """Excute procedure to retrive TOVTS gender data"""
        logger.info("Retrive gender from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_PCODESEXO)
        rows = cursor.fetchall()
        cnxn = external_db.get_connection()
        cnxn.close()
        new_changes: List[EmployeeGenderTotvsSchema] = []
        for row in rows:
            gender_totvs = totvs_to_gender_schema(row)
            if not gender_totvs:
                break
            if verify_changes(
                gender_totvs, EmployeeGenderTotvsSchema, EmployeeGenderTOTVSModel
            ):
                new_changes.append(gender_totvs)
                insert(gender_totvs, EmployeeGenderTOTVSModel)
        end = time()
        elapsed_time = end - start
        logger.info(self.TIME_INFO, str(elapsed_time))
        set_last_sync(len(new_changes), elapsed_time, "gender")
        logger.info("Retrive gender from TOTVS end.")

    def _get_nationality_totvs(self):
        """Excute procedure to retrive TOVTS nationality data"""
        logger.info("Retrive nationality from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_PCODNACAO)
        rows = cursor.fetchall()
        cnxn = external_db.get_connection()
        cnxn.close()
        new_changes: List[EmployeeNationalityTotvsSchema] = []
        for row in rows:
            nationality_totvs = totvs_to_nationality_schema(row)
            if not nationality_totvs:
                break
            if verify_changes(
                nationality_totvs,
                EmployeeNationalityTotvsSchema,
                EmployeeNationalityTOTVSModel,
            ):
                new_changes.append(nationality_totvs)
                insert(nationality_totvs, EmployeeNationalityTOTVSModel)
        end = time()
        elapsed_time = end - start
        logger.info(self.TIME_INFO, str(elapsed_time))
        set_last_sync(len(new_changes), elapsed_time, "nationality")
        logger.info("Retrive nationality from TOTVS end.")

    def _get_cost_center_totvs(self):
        """Excute procedure to retrive TOVTS cost center data"""
        logger.info("Retrive cost center from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_GCCUSTO)
        rows = cursor.fetchall()
        cnxn = external_db.get_connection()
        cnxn.close()
        new_changes: List[CostCenterTotvsSchema] = []
        for row in rows:
            cost_center_totvs = totvs_to_cost_center_schema(row)
            if not cost_center_totvs:
                break
            if verify_changes(
                cost_center_totvs, CostCenterTotvsSchema, CostCenterTOTVSModel
            ):
                new_changes.append(cost_center_totvs)
                insert(cost_center_totvs, CostCenterTOTVSModel)
        end = time()
        elapsed_time = end - start
        logger.info(self.TIME_INFO, str(elapsed_time))
        set_last_sync(len(new_changes), elapsed_time, "cost_center")
        logger.info("Retrive cost center from TOTVS end.")

    def _get_asset_type_totvs(self):
        """Excute procedure to retrive TOVTS asset type data"""
        logger.info("Retrive asset type from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_IGRUPOPATRIMONIO)
        rows = cursor.fetchall()
        cnxn = external_db.get_connection()
        cnxn.close()
        new_changes: List[AssetTypeTotvsSchema] = []
        for row in rows:
            asset_type_totvs = totvs_to_asset_type_schema(row)
            if not asset_type_totvs:
                break
            if verify_changes(
                asset_type_totvs, AssetTypeTotvsSchema, AssetTypeTOTVSModel
            ):
                new_changes.append(asset_type_totvs)
                insert(asset_type_totvs, AssetTypeTOTVSModel)
        end = time()
        elapsed_time = end - start
        logger.info(self.TIME_INFO, str(elapsed_time))
        set_last_sync(len(new_changes), elapsed_time, "asset_type")
        logger.info("Retrive asset type from TOTVS end.")

    def _get_asset_totvs(self):
        """Excute procedure to retrive TOVTS asset data"""
        logger.info("Retrive asset from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_IPATRIMONIO)
        rows = cursor.fetchall()
        cnxn = external_db.get_connection()
        cnxn.close()
        new_changes: List[AssetTotvsSchema] = []
        for row in rows:
            asset_totvs = totvs_to_asset_schema(row)
            if not asset_totvs:
                break
            if verify_changes(asset_totvs, AssetTotvsSchema, AssetTOTVSModel):
                new_changes.append(asset_totvs)
                insert(asset_totvs, AssetTOTVSModel)
        update_asset_totvs(new_changes)
        end = time()
        elapsed_time = end - start
        logger.info(self.TIME_INFO, str(elapsed_time))
        set_last_sync(len(new_changes), elapsed_time, "asset")
        logger.info("Retrive asset from TOTVS end.")

    def _get_role_totvs(self):
        """Excute procedure to retrive TOVTS role data"""
        logger.info("Retrive role from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_PFUNCAO)
        rows = cursor.fetchall()
        cnxn = external_db.get_connection()
        cnxn.close()
        new_changes: List[EmployeeRoleTotvsSchema] = []
        for row in rows:
            role_totvs = totvs_to_role_schema(row)
            if not role_totvs:
                break
            if verify_changes(
                role_totvs, EmployeeRoleTotvsSchema, EmployeeRoleTOTVSModel
            ):
                new_changes.append(role_totvs)
                insert(role_totvs, EmployeeRoleTOTVSModel)
        end = time()
        elapsed_time = end - start
        logger.info(self.TIME_INFO, str(elapsed_time))
        set_last_sync(len(new_changes), elapsed_time, "role")
        logger.info("Retrive role from TOTVS end.")

    def read_totvs_db(self):
        """Excute procedure to retrive TOVTS data"""
        logger.info("Retrive from TOTVS start.")
        self._get_asset_type_totvs()
        self._get_marital_status_totvs()
        self._get_gender_totvs()
        self._get_nationality_totvs()
        self._get_cost_center_totvs()
        self._get_role_totvs()
        self._get_educational_level_totvs()
        self._get_asset_totvs()
        self._get_employees_totvs()
        logger.info("Retrive from TOTVS end.")

    def force_fetch(self) -> None:
        """Force fetch from TOTVS database"""
        if self._force:
            logger.info("Force retrive.")
            self.read_totvs_db()
        else:
            logger.info("Cannot force.")
