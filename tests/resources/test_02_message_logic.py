import unittest
from mib import create_app
import responses
#from mib import db
from flask_sqlalchemy import SQLAlchemy
import datetime

tested_app = create_app()


class LogicTest(unittest.TestCase):
    from mib.logic.message_logic import MessageLogic

    msg_logic = MessageLogic()

    test_message_id = 4
    test_draft_id = 5
    
    def test_00_populate(self):
        from mib.models.message import Message
        from mib.models.message import Message_Recipient
        from mib.dao.message_manager import MessageManager
        
        with tested_app.app_context():
            # delivered/received message from 10 to 11
            message = Message()
            message.sender_id = 10
            message.content = 'Delivered: from 10 to 11'
            message.deliver_time = datetime.datetime.fromisoformat('2010-10-25 15:00')
            message.image = '' 
            message.is_sent = True
            message.is_delivered = True

            MessageManager.create_message(message)

            message_recipient = Message_Recipient()
            message_recipient.id = message.id
            message_recipient.recipient_id = 11
            message_recipient.is_read = False
            message_recipient.is_hide = False

            MessageManager.create_message_recipient(message_recipient)

            self.test_message_id = message.id
            
            # drafts message from 10 to 11
            draft = Message()
            draft.sender_id = 10
            draft.content = 'Draft: from 10 to 11'
            draft.deliver_time = datetime.datetime.fromisoformat('2010-10-25 15:00')
            draft.image = '' 
            draft.is_sent = False
            draft.is_delivered = False

            MessageManager.create_message(draft)

            draft_recipient = Message_Recipient()
            draft_recipient.id = draft.id
            draft_recipient.recipient_id = 11
            draft_recipient.is_read = False
            draft_recipient.is_hide = False

            MessageManager.create_message_recipient(draft_recipient)

            self.test_draft_id = message.id


    def test_01_get_received_message(self):

        # 404 message doesn't exist
        # 403 not recipient
        # 404 message is hide
        # 500 user is not activa
        # mocking
        # send email in reading first time
        # 500 blacklist is not available
        # success with content filter enable
        # success with content filter disable

        pass

    def test_02_get_draft_message(self):
        pass

    def test_03_get_pending_or_delivered_message(self):
        pass
    
    def test_04_delete_message(self):
        pass