from mib import db

class Report(db.Model):
    """Representation of Report model."""

    # The name of the table that we explicitly set
    __tablename__ = 'Report'

    # A list of fields to be serialized TODO da fare
    SERIALIZE_LIST = ['id', 'email', 'is_active', 'is_anonymous','firstname','lastname','date_of_birth','lottery_points','has_picture','content_filter_enabled']

    reporting_user_id = db.Column(db.Integer, nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('Message.id'), nullable=False)
    report_time = db.Column(db.DateTime)

    __table_args__ = (
        db.PrimaryKeyConstraint(
            reporting_user_id, message_id,
        ),
    )

    def __init__(self, *args, **kw):
        super(Report, self).__init__(*args, **kw)
    
    def serialize(self):
        return dict([(k, self.__getattribute__(k)) for k in self.SERIALIZE_LIST])
