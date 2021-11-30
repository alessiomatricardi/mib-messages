from mib.dao.manager import Manager
from mib.models.report import Report


class ReportManager(Manager):

    @staticmethod
    def is_message_reported(message_id, user_id) -> bool:

        Manager.check_none(message_id=message_id)
        Manager.check_none(user_id=user_id)

        query = Report.query.filter(
            Report.message_id == message_id, 
            Report.reporting_user_id == user_id
        ).first()

        return query is not None