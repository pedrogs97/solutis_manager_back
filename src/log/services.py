"""Log services"""
from sqlalchemy.orm import Session

from src.auth.models import UserModel
from src.log.models import LogModel


class LogService:
    """Log services"""

    def set_log(
        self,
        module: str,
        model: str,
        operation: str,
        identifier: int,
        user: UserModel,
        db_session: Session,
    ):
        """Set a log from a operation"""
        new_log = LogModel(
            user=user,
            module=module,
            model=model,
            operation=operation,
            identifier=identifier,
        )

        db_session.add(new_log)
        db_session.commit()
