from mib import db
from .message_recipient import Message_Recipient
from .report import Report

class Message(db.Model):
    """Representation of Message model."""

    # The name of the table that we explicitly set
    __tablename__ = 'Message'

    # A list of fields to be serialized TODO da fare
    SERIALIZE_LIST = ['id', 'email', 'is_active', 'is_anonymous','firstname','lastname','date_of_birth','lottery_points','has_picture','content_filter_enabled']


    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Unicode(700), nullable=False)
    is_sent = db.Column(db.Boolean, default = False) 
    is_delivered = db.Column(db.Boolean, default = False)
    deliver_time = db.Column(db.DateTime)
    image = db.Column(db.Unicode(700), default="") # the name of the attached file

    # Relatioship with other classes
    recipients = db.relation('Message_Recipient', backref='Message_Recipient.recipient_id', lazy=True)
    reports = db.relation('Report', backref='Report', lazy=True)

    def __init__(self, *args, **kw):
        super(Message, self).__init__(*args, **kw)

    def set_sender(self, id):
        self.sender_id = id

    def set_content(self, content):
        self.content = content

    #
    # TODO add setter methods to set the deliver_time and the is_sent variables
    #

    def get_id(self):
        return self.id
    
    def get_obj(self):
        message_obj = {
            'id': self.id,
            'sender_id': self.sender_id,
            'content': self.content,
            'is_sent': self.is_sent,
            'is_delivered': self.is_delivered,
            'deliver_time': self.deliver_time
        }
        return message_obj

    def serialize(self):
        return dict([(k, self.__getattribute__(k)) for k in self.SERIALIZE_LIST])
