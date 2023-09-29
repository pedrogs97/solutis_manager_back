"""Service client"""
from typing import List
import logging
import requests
from datasync.config import AGILE_HOST
from datasync.schemas import (
    CostCenterTotvsSchema,
    AssetTypeTotvsSchema,
    AssetTotvsSchema,
    EmployeeMatrimonialStatusTotvsSchema,
    EmployeeGenderTotvsSchema,
    EmployeeNationalityTotvsSchema,
    EmployeeRoleTotvsSchema,
    EmployeeTotvsSchema,
)


logger = logging.getLogger(__name__)


class AgileClient:
    """Agile client"""

    def send_cost_center_updates(
        self, update_data: List[CostCenterTotvsSchema]
    ) -> None:
        """Send cost center updates to Agile"""
        respose = requests.post(
            url=f"{AGILE_HOST}cost-center/update/",
            data=[cc.model_dump() for cc in update_data],
            timeout=500,
        )
        if respose.status_code == 200:
            logger.info("Cost center update sent successfully")
            return

        logger.warning("Cost center update fail. Erro: %s", respose.json()["detail"])

    def send_asset_type_updates(self, update_data: List[AssetTypeTotvsSchema]) -> None:
        """Send asset types updates to Agile"""
        respose = requests.post(
            url=f"{AGILE_HOST}asset-type/update/",
            data=[cc.model_dump() for cc in update_data],
            timeout=500,
        )
        if respose.status_code == 200:
            logger.info("Asset types update sent successfully")
            return

        logger.warning("Asset types update fail. Erro: %s", respose.json()["detail"])

    def send_asset_updates(self, update_data: List[AssetTotvsSchema]) -> None:
        """Send asset updates to Agile"""
        respose = requests.post(
            url=f"{AGILE_HOST}asset/update/",
            data=[cc.model_dump() for cc in update_data],
            timeout=500,
        )
        if respose.status_code == 200:
            logger.info("Asset update sent successfully")
            return

        logger.warning("Asset update fail. Erro: %s", respose.json()["detail"])

    def send_matrimonial_status_updates(
        self, update_data: List[EmployeeMatrimonialStatusTotvsSchema]
    ) -> None:
        """Send matrimonial status updates to Agile"""
        respose = requests.post(
            url=f"{AGILE_HOST}employee/matrimonial-status/update/",
            data=[cc.model_dump() for cc in update_data],
            timeout=500,
        )
        if respose.status_code == 200:
            logger.info("Matrimonial status update sent successfully")
            return

        logger.warning(
            "Matrimonial status update fail. Erro: %s", respose.json()["detail"]
        )

    def send_gender_updates(self, update_data: List[EmployeeGenderTotvsSchema]) -> None:
        """Send gender updates to Agile"""
        respose = requests.post(
            url=f"{AGILE_HOST}employee/gender/update/",
            data=[cc.model_dump() for cc in update_data],
            timeout=500,
        )
        if respose.status_code == 200:
            logger.info("Gender update sent successfully")
            return

        logger.warning("Gender update fail. Erro: %s", respose.json()["detail"])

    def send_nationality_updates(
        self, update_data: List[EmployeeNationalityTotvsSchema]
    ) -> None:
        """Send nationality updates to Agile"""
        respose = requests.post(
            url=f"{AGILE_HOST}employee/nationality/update/",
            data=[cc.model_dump() for cc in update_data],
            timeout=500,
        )
        if respose.status_code == 200:
            logger.info("Nationality update sent successfully")
            return

        logger.warning("Nationality update fail. Erro: %s", respose.json()["detail"])

    def send_role_updates(self, update_data: List[EmployeeRoleTotvsSchema]) -> None:
        """Send role updates to Agile"""
        respose = requests.post(
            url=f"{AGILE_HOST}employee/role/update/",
            data=[cc.model_dump() for cc in update_data],
            timeout=500,
        )
        if respose.status_code == 200:
            logger.info("Role update sent successfully")
            return

        logger.warning("Role update fail. Erro: %s", respose.json()["detail"])

    def send_employee_updates(self, update_data: List[EmployeeTotvsSchema]) -> None:
        """Send employee updates to Agile"""
        respose = requests.post(
            url=f"{AGILE_HOST}employee/update/",
            data=[cc.model_dump() for cc in update_data],
            timeout=500,
        )
        if respose.status_code == 200:
            logger.info("Employee update sent successfully")
            return

        logger.warning("Employee update fail. Erro: %s", respose.json()["detail"])
