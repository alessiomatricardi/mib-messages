from mib import db

class Message_Recipient(db.Model):
    """Representation of Message_Recipient model."""

    # The name of the table that we explicitly set
    __tablename__ = 'Message_Recipient'

    # A list of fields to be serialized
    SERIALIZE_LIST = ['id', 'recipient_id', 'is_read', 'is_hide']

    id = db.Column(db.Integer, db.ForeignKey('Message.id'), nullable=False)
    recipient_id = db.Column(db.Integer, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_hide = db.Column(db.Boolean, default = False) # message has been cancelled by the recipient

    __table_args__ = (
        db.PrimaryKeyConstraint(
            id, recipient_id,
        ),
    )

    def __init__(self, *args, **kw):
        super(Message_Recipient, self).__init__(*args, **kw)

    def get_id(self):
        return self.id

    def get_recipient_id(self):
        return self.recipient_id
    
    def get_recipient_obj(self):
        return {
            'id': self.id,
            'recipient_id': self.recipient_id,
            'is_read': self.is_read
            #'read_time': self.read_time
        }
    
    def serialize(self):
        return dict([(k, self.__getattribute__(k)) for k in self.SERIALIZE_LIST])
