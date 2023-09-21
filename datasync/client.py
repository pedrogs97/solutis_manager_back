"""Service client"""
import logging
import requests
from datasync.config import AGILE_HOST


logger = logging.getLogger(__name__)


class AgileClient:
    """Agile client"""

    def send_updates(self, data: dict) -> None:
        """Send update to Agile service"""
        respose = requests.post(url=AGILE_HOST, data=data)
        if respose.status_code == 200:
            logger.info("Update sent succefuly")
        else:
            logger.warning("Update fail. Erro: %s", respose.json()["detail"])
