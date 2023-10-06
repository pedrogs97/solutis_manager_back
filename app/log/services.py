"""Log services"""
from app.backends import Session_db
from app.auth.models import UserModel
from app.log.models import LogModel


class LogService:
    """Log services"""

    def set_log(
        self, module: str, model: str, operation: str, identifier: int, user: UserModel
    ):
        """Set a log from a operation"""
        with Session_db() as db_session:
            new_log = LogModel(
                user=user,
                module=module,
                model=model,
                operation=operation,
                identifier=identifier,
            )

            db_session.add(new_log)
            db_session.commit()
