from mib.dao.manager import Manager
from mib.models.report import Report
from sqlalchemy import and_
import datetime


class ReportManager(Manager):

    @staticmethod
    def create_report(report: Report):
        Manager.create(report=report)

    @staticmethod
    def is_message_reported(message_id, user_id) -> bool:

        Manager.check_none(message_id=message_id)
        Manager.check_none(user_id=user_id)

        query = Report.query.filter(and_(Report.message_id == message_id, Report.reporting_user_id == user_id)).first()

        if query is None:
            return False
        else: 
            return True

    