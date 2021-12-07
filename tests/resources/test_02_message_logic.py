import unittest
from mib import create_app
import responses
#from mib import db
from flask_sqlalchemy import SQLAlchemy
import datetime
from mib.logic.user import User

tested_app = create_app()

USERS_ENDPOINT = tested_app.config['USERS_MS_URL']
BLACKLIST_ENDPOINT = tested_app.config['BLACKLIST_MS_URL']


class LogicTest(unittest.TestCase):
    from mib.logic.message_logic import MessageLogic

    msg_logic = MessageLogic()

    sender_json = {
            'id':10, 
            'email':'prova10@mail.com', 
            'is_active':True, 
            'firstname':'Decimo',
            'lastname':'Meridio',
            'date_of_birth':'1996-06-06',
            'lottery_points':0,
            'has_picture':False,
            'content_filter_enabled':False
        }

    sender_json_content_filter = {
            'id':10, 
            'email':'prova10@mail.com', 
            'is_active':True, 
            'firstname':'Decimo',
            'lastname':'Meridio',
            'date_of_birth':'1996-06-06',
            'lottery_points':0,
            'has_picture':False,
            'content_filter_enabled':True
        }

    recipient_json = {
        'id':11, 
        'email':'prova11@mail.com', 
        'is_active':True, 
        'firstname':'Undici',
        'lastname':'Leoni',
        'date_of_birth':'1926-03-21',
        'lottery_points':0,
        'has_picture':False,
        'content_filter_enabled':False
    }

    recipient_json_content_filter = {
        'id':11, 
        'email':'prova11@mail.com', 
        'is_active':True, 
        'firstname':'Undici',
        'lastname':'Leoni',
        'date_of_birth':'1926-03-21',
        'lottery_points':0,
        'has_picture':False,
        'content_filter_enabled':True
    }

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

    @responses.activate
    def test_01_get_received_message(self):
        from mib.models.message import Message
        from mib.models.message import Message_Recipient
        from mib.dao.message_manager import MessageManager

        with tested_app.app_context():

            received_message = MessageManager.retrieve_message_by_id('received',self.test_message_id)
            non_existing_message = MessageManager.retrieve_message_by_id('received',1000)

            self.assertEqual(received_message.sender_id,self.sender_json['id'])

            requester = User.build_from_json(self.recipient_json)
            wrong_requester =  User.build_from_json(self.sender_json)
            requester_content_filter = User.build_from_json(self.recipient_json_content_filter)

            # 404 message doesn't exist
            result, code = self.msg_logic.get_received_message(non_existing_message,requester)
            self.assertEqual(code,404)

            # 403 not recipient
            result, code = self.msg_logic.get_received_message(received_message,wrong_requester)
            self.assertEqual(code,403)
            
            # 500 user ma is not active
            result, code = self.msg_logic.get_received_message(received_message,requester)
            self.assertEqual(code,500)

            # mocking users
            responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(10)),
                    json={'status': 'Current user present','user':self.sender_json}, status=404)

            responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(11)),
                    json={'status': 'Current user present','user':self.recipient_json}, status=200)

            # failure 404 when sender is not found
            result, code = self.msg_logic.get_received_message(received_message,requester)
            self.assertEqual(code,404)
            
            # now the sender exists
            responses.replace(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(10)),
                    json={'status': 'Current user present','user':self.sender_json}, status=200)

            
            # send email in reading first time but 500 blacklist is not available
            result, code = self.msg_logic.get_received_message(received_message,requester)
            self.assertEqual(code,500)
            
            # mocking blacklist but it returns 500
            responses.add(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                    json={'status': 'Current user present','blacklist':[]}, status=500)

            # failure 500 when blacklist returns an Internal Server Error
            result, code = self.msg_logic.get_received_message(received_message,requester)
            self.assertEqual(code,500)
            
            # now the blacklist microservice returns 200 
            responses.replace(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                    json={'status': 'Current user present','blacklist':[]}, status=200)
            
            # success with content filter disable
            result, code = self.msg_logic.get_received_message(received_message,requester)
            self.assertEqual(code,200)
            
            # enabling content filter
            responses.replace(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(11)),
                    json={'status': 'Current user present','user':self.recipient_json_content_filter}, status=200)

            # success with content filter enable
            result, code = self.msg_logic.get_received_message(received_message,requester_content_filter)
            self.assertEqual(code,200)

            # 404 message is hide
            message_recipient = MessageManager.retrieve_message_recipient(received_message.id,requester.id)
            MessageManager.hide_message(message_recipient)
            result, code = self.msg_logic.get_received_message(received_message,requester)
            self.assertEqual(code,404)

    @responses.activate
    def test_02_get_draft_message(self):
        from mib.dao.message_manager import MessageManager

        with tested_app.app_context():

            draft_message = MessageManager.retrieve_message_by_id('drafts',self.test_draft_id)
            non_existing_message = MessageManager.retrieve_message_by_id('drafts',1000)

            self.assertEqual(draft_message.sender_id,self.sender_json['id'])

            requester = User.build_from_json(self.sender_json)
            wrong_requester =  User.build_from_json(self.recipient_json)

            # message not found
            result, code = self.msg_logic.get_draft_message(non_existing_message,requester)
            self.assertEqual(code,404)

            # not the sender 403
            result, code = self.msg_logic.get_draft_message(draft_message,wrong_requester)
            self.assertEqual(code,403)

            # 500 blacklist not active
            result, code = self.msg_logic.get_draft_message(draft_message,requester)
            self.assertEqual(code,500)

            # mocking blacklist
            responses.add(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                    json={'status': 'Current user present','blacklist':[]}, status=500)

            # 500 when blacklist returns an Internal Server Error
            result, code = self.msg_logic.get_draft_message(draft_message,requester)
            self.assertEqual(code,500)

            # mocking blacklist
            responses.replace(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                    json={'status': 'Current user present','blacklist':[]}, status=200)

            # 500 users not active while checking that the recipients previously selected exist
            result, code = self.msg_logic.get_draft_message(draft_message,requester)
            self.assertEqual(code,500)

            # mocking users but it returns 404
            responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(10)),
                    json={'status': 'Current user present','user':self.sender_json}, status=200)

            responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(11)),
                    json={'status': 'Current user present','user':self.recipient_json}, status=404)

            # fail 404 when recipient not found
            result, code = self.msg_logic.get_draft_message(draft_message,requester)
            self.assertEqual(code,404)

            # now recipient users returns 200
            responses.replace(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(11)),
                    json={'status': 'Current user present','user':self.recipient_json}, status=200)

            # previous recipients are either in the blacklist or not active
            responses.replace(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                    json={'status': 'Current user present','blacklist':[11]}, status=200)

            # 200 success
            result, code = self.msg_logic.get_draft_message(draft_message,requester)
            self.assertEqual(code,200)


    @responses.activate
    def test_03_get_pending_or_delivered_message(self):
        from mib.dao.message_manager import MessageManager

        with tested_app.app_context():

            delivered_message = MessageManager.retrieve_message_by_id('delivered',self.test_message_id)
            non_existing_message = MessageManager.retrieve_message_by_id('delivered',1000)

            self.assertEqual(delivered_message.sender_id,self.sender_json['id'])

            requester = User.build_from_json(self.sender_json)
            requester_content_filter = User.build_from_json(self.sender_json_content_filter)
            wrong_requester =  User.build_from_json(self.recipient_json)

            # message not found
            result, code = self.msg_logic.get_pending_or_delivered_message(non_existing_message,requester)
            self.assertEqual(code,404)

            # not the sender 403
            result, code = self.msg_logic.get_pending_or_delivered_message(delivered_message,wrong_requester)
            self.assertEqual(code,403)

            # 500 blacklist not active
            result, code = self.msg_logic.get_pending_or_delivered_message(delivered_message,requester)
            self.assertEqual(code,500)

            # mocking blacklist
            responses.add(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                    json={'status': 'Current user present','blacklist':[]}, status=500)

            # 500 when blacklist returns an Internal Server Error
            result, code = self.msg_logic.get_pending_or_delivered_message(delivered_message,requester)
            self.assertEqual(code,500)

            # mocking blacklist
            responses.replace(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                    json={'status': 'Current user present','blacklist':[]}, status=200)

            # 500 users not active while checking that the recipients previously selected exist
            result, code = self.msg_logic.get_pending_or_delivered_message(delivered_message,requester)
            self.assertEqual(code,500)

            # mocking users but it returns 404
            responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(10)),
                    json={'status': 'Current user present','user':self.sender_json}, status=200)

            responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(11)),
                    json={'status': 'Current user present','user':self.recipient_json}, status=404)

            # fail 404 when recipient not found
            result, code = self.msg_logic.get_pending_or_delivered_message(delivered_message,requester)
            self.assertEqual(code,404)

            # now recipient users returns 200
            responses.replace(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(11)),
                    json={'status': 'Current user present','user':self.recipient_json}, status=200)

            # previous recipients are either in the blacklist or not active
            responses.replace(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                    json={'status': 'Current user present','blacklist':[11]}, status=200)

            # now the sender has content filter enabled 
            responses.replace(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(10)),
                    json={'status': 'Current user present','user':self.sender_json_content_filter}, status=200)

            # 200 success
            result, code = self.msg_logic.get_pending_or_delivered_message(delivered_message,requester_content_filter)
            self.assertEqual(code,200)

    
    @responses.activate
    def test_04_delete_message(self):
        from mib.dao.message_manager import MessageManager

        with tested_app.app_context():

            draft_message = MessageManager.retrieve_message_by_id('drafts',self.test_draft_id)
            non_existing_message = MessageManager.retrieve_message_by_id('drafts',1000)

            self.assertEqual(draft_message.sender_id,self.sender_json['id'])

            requester = User.build_from_json(self.sender_json)
            wrong_requester =  User.build_from_json(self.recipient_json)

            # message not found
            result, code = self.msg_logic.delete_message(non_existing_message,requester)
            self.assertEqual(code,404)

            # 403 sender not corresponing
            result, code = self.msg_logic.delete_message(draft_message,wrong_requester)
            self.assertEqual(code,403)

            # 200 success
            result, code = self.msg_logic.delete_message(draft_message,requester)
            self.assertEqual(code,403)
