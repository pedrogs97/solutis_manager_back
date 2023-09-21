"""Scheduler Service"""
import logging
from time import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers import (
    SchedulerNotRunningError,
    SchedulerAlreadyRunningError,
)
from datasync.database import ExternalDatabase
from datasync.config import DATABASE_URL
from datasync.service import (
    totvs_to_employee_schema,
    verify_changes_empolyee,
    insert_employee,
    set_last_sync,
    totvs_to_gender_schema,
    totvs_to_matrimonial_status_schema,
    totvs_to_nationality_schema,
    totvs_to_cost_center_schema,
    totvs_to_asset_type_schema,
    totvs_to_asset_schema,
    totvs_to_role_schema,
    verify_changes_gender,
    verify_changes_matrimonial_status,
    verify_changes_nationality,
    verify_changes_cost_center,
    verify_changes_asset_type,
    verify_changes_asset,
    verify_changes_role,
    insert_gender,
    insert_matrimonial_status,
    insert_nationality,
    insert_cost_center,
    insert_asset_type,
    insert_asset,
    insert_role,
)

logger = logging.getLogger(__name__)


class SchedulerService:
    """Scheduler Service class"""

    SQL_PPESSOA = """SELECT
	p.CODIGO, p.NOME, p.DTNASCIMENTO, c.DESCRICAO AS CIVIL, s.DESCRICAO AS SEXO, 
    n.DESCRICAO AS NACIONALIDADE, p.RUA, p.NUMERO, p.COMPLEMENTO, p.BAIRRO,
    p.ESTADO, p.CIDADE, p.CEP, p.PAIS, p.CPF, p.TELEFONE1, p.CARTIDENTIDADE,
    p.UFCARTIDENT, p.ORGEMISSORIDENT, p.DTEMISSAOIDENT, p.EMAIL, pf.NOME AS CARGO
    FROM CorporeRM_SI.dbo.PPESSOA as p 
    LEFT JOIN PCODESTCIVIL AS c
    ON p.ESTADOCIVIL = c.CODINTERNO
    LEFT JOIN PCODSEXO AS s
    ON p.SEXO = s.CODINTERNO
    LEFT JOIN PCODNACAO n
    ON n.CODINTERNO = p.NACIONALIDADE 
    LEFT JOIN PFUNC as f
    ON f.CODPESSOA = p.CODIGO
    LEFT JOIN PFUNCAO as pf
    ON f.CODFUNCAO = pf.CODIGO ;"""

    SQL_PCODESTCIVIL = """SELECT DESCRICAO, CODINTERNO FROM PCODESTCIVIL;"""

    SQL_PCODESEXO = """SELECT DESCRICAO, CODINTERNO FROM PCODSEXO;"""

    SQL_PCODNACAO = """SELECT DESCRICAO, CODINTERNO FROM PCODNACAO;"""

    SQL_GCCUSTO = """SELECT cc.CODREDUZIDO, cc.NOME, cls.DESCRICAO
    FROM CorporeRM_SI.dbo.GCCUSTO cc 
    LEFT JOIN CCLASSIFICACC AS cls 
    ON cls.CODCLASSIFICA = cc.CODCLASSIFICA
    WHERE cc.CODCOLIGADA = 1;"""

    SQL_IPATRIMONIO = """SELECT p.IDPATRIMONIO, p.DESCRICAO, g.DESCRICAO AS TIPO,
    p.ATIVO, p.DATAAQUISICAO, p.PATRIMONIO, p.QUANTIDADE, p.UNIDADE, p.OBSERVACOES,
    p.CODIGOBARRA, c.NOME AS CENTROCUSTO, p.VALORBASE, p.VRDEPACUCORRIGIDA, pc.SERIE,
    pc.IMEI, pc.ACESSORIOS, pc.OPERADORA, pc.SISTEMAOPERACIONAL, pc.PACOTEOFFICE,
    pc.PADRAOEQUIP, ga.DATAEXPIRACAO AS GARANTIA, pc.MANUT5 AS LINHA, f.NOMEFANTASIA as FORNECEDOR
    FROM CorporeRM_SI.dbo.IPATRIMONIO AS p
    LEFT JOIN IGRUPOPATRIMONIO AS g
    ON g.IDGRUPOPATRIMONIO = p.IDGRUPOPATRIMONIO 
    LEFT JOIN GCCUSTO AS c
    ON P.CODCENTROCUSTO = c.CODCCUSTO 
    LEFT JOIN IPATRIMONIOCOMPL AS pc
    ON pc.IDPATRIMONIO = p.IDPATRIMONIO 
    LEFT JOIN IGARANTIA AS ga
    ON ga.IDPATRIMONIO = p.IDPATRIMONIO 
    LEFT JOIN FCFO as f
    ON f.CODCFO = p.CODFORNECEDOR 
    WHERE (p.CODCOLIGADA = 1)"""

    SQL_IGRUPOPATRIMONIO = """SELECT IDGRUPOPATRIMONIO, CODGRUPOPATRIMONIO, DESCRICAO
    FROM IGRUPOPATRIMONIO 
    WHERE CODCOLIGADA = 1"""

    SQL_PFUNCAO = """SELECT CODIGO, NOME
    FROM PFUNCAO 
    WHERE CODCOLIGADA = 1"""

    _scheduler = None

    def __init__(self, debug=False, force=False) -> None:
        self._force = force
        if self._scheduler is None:
            jobstores = {"default": SQLAlchemyJobStore(url=DATABASE_URL)}
            self._scheduler = self._scheduler = AsyncIOScheduler(
                jobstores=jobstores,
            )
            self._debug = debug
            if debug:
                self._trigger = "interval"
                self._minute = "*/5"
            else:
                self._trigger = "cron"
                self._hour = "12-18"
                self._minute = "0"

    def _get_employees_totvs(self):
        """Excute procedure to retrive TOVTS emplyoee data"""
        logger.info("Retrive employee from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_PPESSOA)
        rows = cursor.fetchall()
        new_changes = 0
        for row in rows:
            employee_totvs = totvs_to_employee_schema(row)
            if not employee_totvs:
                break
            if verify_changes_empolyee(employee_totvs):
                new_changes += 1
                insert_employee(employee_totvs)

        end = time()
        elapsed_time = end - start
        logger.info("Execution time: %s ms", str(elapsed_time))
        set_last_sync(new_changes, elapsed_time, "employee")
        logger.info("Retrive employee from TOTVS end.")

    def _get_matrimonial_status_totvs(self):
        """Excute procedure to retrive TOVTS matrimonial status data"""
        logger.info("Retrive matrimonial status from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_PCODESTCIVIL)
        rows = cursor.fetchall()
        new_changes = 0
        for row in rows:
            matrimonial_status_totvs = totvs_to_matrimonial_status_schema(row)
            if not matrimonial_status_totvs:
                break
            if verify_changes_matrimonial_status(matrimonial_status_totvs):
                new_changes += 1
                insert_matrimonial_status(matrimonial_status_totvs)

        end = time()
        elapsed_time = end - start
        logger.info("Execution time: %s ms", str(elapsed_time))
        set_last_sync(new_changes, elapsed_time, "matrimonial_status")
        logger.info("Retrive matrimonial status from TOTVS end.")

    def _get_gender_totvs(self):
        """Excute procedure to retrive TOVTS gender data"""
        logger.info("Retrive gender from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_PCODESEXO)
        rows = cursor.fetchall()
        new_changes = 0
        for row in rows:
            gender_totvs = totvs_to_gender_schema(row)
            if not gender_totvs:
                break
            if verify_changes_gender(gender_totvs):
                new_changes += 1
                insert_gender(gender_totvs)

        end = time()
        elapsed_time = end - start
        logger.info("Execution time: %s ms", str(elapsed_time))
        set_last_sync(new_changes, elapsed_time, "gender")
        logger.info("Retrive gender from TOTVS end.")

    def _get_nacionality_totvs(self):
        """Excute procedure to retrive TOVTS nationality data"""
        logger.info("Retrive nationality from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_PCODNACAO)
        rows = cursor.fetchall()
        new_changes = 0
        for row in rows:
            nationality_totvs = totvs_to_nationality_schema(row)
            if not nationality_totvs:
                break
            if verify_changes_nationality(nationality_totvs):
                new_changes += 1
                insert_nationality(nationality_totvs)

        end = time()
        elapsed_time = end - start
        logger.info("Execution time: %s ms", str(elapsed_time))
        set_last_sync(new_changes, elapsed_time, "nationality")
        logger.info("Retrive nationality from TOTVS end.")

    def _get_cost_center_totvs(self):
        """Excute procedure to retrive TOVTS cost center data"""
        logger.info("Retrive cost center from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_GCCUSTO)
        rows = cursor.fetchall()
        new_changes = 0
        for row in rows:
            cost_center_totvs = totvs_to_cost_center_schema(row)
            if not cost_center_totvs:
                break
            if verify_changes_cost_center(cost_center_totvs):
                new_changes += 1
                insert_cost_center(cost_center_totvs)

        end = time()
        elapsed_time = end - start
        logger.info("Execution time: %s ms", str(elapsed_time))
        set_last_sync(new_changes, elapsed_time, "cost_center")
        logger.info("Retrive cost center from TOTVS end.")

    def _get_asset_type_totvs(self):
        """Excute procedure to retrive TOVTS asset type data"""
        logger.info("Retrive asset type from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_IGRUPOPATRIMONIO)
        rows = cursor.fetchall()
        new_changes = 0
        for row in rows:
            asset_type_totvs = totvs_to_asset_type_schema(row)
            if not asset_type_totvs:
                break
            if verify_changes_asset_type(asset_type_totvs):
                new_changes += 1
                insert_asset_type(asset_type_totvs)

        end = time()
        elapsed_time = end - start
        logger.info("Execution time: %s ms", str(elapsed_time))
        set_last_sync(new_changes, elapsed_time, "asset_type")
        logger.info("Retrive asset type from TOTVS end.")

    def _get_asset_totvs(self):
        """Excute procedure to retrive TOVTS asset data"""
        logger.info("Retrive asset from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_IPATRIMONIO)
        rows = cursor.fetchall()
        new_changes = 0
        for row in rows:
            asset_totvs = totvs_to_asset_schema(row)
            if not asset_totvs:
                break
            if verify_changes_asset(asset_totvs):
                new_changes += 1
                insert_asset(asset_totvs)

        end = time()
        elapsed_time = end - start
        logger.info("Execution time: %s ms", str(elapsed_time))
        set_last_sync(new_changes, elapsed_time, "asset")
        logger.info("Retrive asset from TOTVS end.")

    def _get_role_totvs(self):
        """Excute procedure to retrive TOVTS role data"""
        logger.info("Retrive role from TOTVS start.")
        start = time()
        external_db = ExternalDatabase()
        cursor = external_db.get_cursor()
        cursor.execute(self.SQL_PFUNCAO)
        rows = cursor.fetchall()
        new_changes = 0
        for row in rows:
            role_totvs = totvs_to_role_schema(row)
            if not role_totvs:
                break
            if verify_changes_role(role_totvs):
                new_changes += 1
                insert_role(role_totvs)

        end = time()
        elapsed_time = end - start
        logger.info("Execution time: %s ms", str(elapsed_time))
        set_last_sync(new_changes, elapsed_time, "role")
        logger.info("Retrive role from TOTVS end.")

    def _read_totvs_db(self):
        """Excute procedure to retrive TOVTS data"""
        logger.info("Retrive from TOTVS start.")
        self._get_employees_totvs()
        self._get_matrimonial_status_totvs()
        self._get_gender_totvs()
        self._get_nacionality_totvs()
        self._get_asset_totvs()
        self._get_asset_type_totvs()
        self._get_cost_center_totvs()
        self._get_role_totvs()
        logger.info("Retrive from TOTVS end.")

    def start(self) -> None:
        """Start Scheduler Service"""
        try:
            if self._scheduler is None:
                return

            self._scheduler.start()
            logger.info("Started Scheduler Service.")
        except SchedulerAlreadyRunningError:
            logger.warning("Scheduler Service running.")
        except Exception as err:
            logger.error("Unable to start Scheduler Service. Error: %s", err.args[0])

    def shutdown(self) -> None:
        """Shutdown Schduler Service"""
        try:
            self._scheduler.shutdown(wait=True)
            self._scheduler = None
            logger.info("Disabled Scheduler Service.")
        except SchedulerNotRunningError:
            logger.warning("Scheduler Service not running.")
        except Exception as err:
            logger.error(
                "Warning: Unable to shutdown Scheduler Service. Error: %s", err.args[0]
            )

    def schedule_job(self) -> None:
        """Create job for read TOTVS db"""
        if self._debug:
            # -- configuração teste - roda a cada 5 min
            # "interval",
            # minute='*/5',
            self._scheduler.add_job(
                self._read_totvs_db,
                # -- configuração de prod/homol - roda todos os dias as 12:00 e 18:00
                self._trigger,
                minute=self._minute,
                # Using max_instances=1 guarantees that only one job
                # runs at the same time (in this event loop).
                max_instances=1,
            )
        else:
            # -- configuração de prod/homol - roda todos os dias as 12:00 e 18:00
            self._scheduler.add_job(
                self._read_totvs_db,
                self._trigger,
                hour=self._hour,
                minute=self._minute,
                # Using max_instances=1 guarantees that only one job
                # runs at the same time (in this event loop).
                max_instances=1,
            )

    def force_fetch(self) -> None:
        """Force fetch from TOTVS database"""
        if self._force:
            logger.info("Force retrive.")
            self._read_totvs_db()
        else:
            logger.info("Cannot force.")
