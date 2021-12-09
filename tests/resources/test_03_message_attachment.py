import unittest
from mib import create_app
import responses, requests
#from mib import db
from flask_sqlalchemy import SQLAlchemy
import datetime
from mib.logic.user import User
import os
import base64
from io import BytesIO
from PIL import Image

basepath = os.path.join(os.getcwd(), 'mib', 'static', 'attachments')

tested_app = create_app()

USERS_ENDPOINT = tested_app.config['USERS_MS_URL']
BLACKLIST_ENDPOINT = tested_app.config['BLACKLIST_MS_URL']


class AttachmentTest(unittest.TestCase):

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

    attachment = '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'
            

    test_message_id = 0
    test_draft_id = 0

    @responses.activate
    def test_01_message_with_attachment(self):
        
        app = tested_app.test_client()

        # data of new message
        new_message_with_attachment_data = {
            'requester_id': self.sender_json['id'],
            'content' : 'attachment!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [self.recipient_json['email']],
            'image': self.attachment,
            'image_filename' : 'attachment.jpg',
            'is_draft': False
        }

        new_message_without_attachment_data = {
            'requester_id': self.sender_json['id'],
            'content' : 'attachment!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [self.recipient_json['email']],
            'image': '',
            'image_filename' : '',
            'is_draft': False
        }


        # mocking blacklist and existance of sender and recipient
        responses.add(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                    json={
                        "blocked": [],
                        "blocking": [],
                        "description": "Blacklist successfully retrieved",
                        "status": "success"
                    }, status=200)

        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(self.sender_json['id'])),
                  json={'status': 'User present', 'user':self.sender_json}, status=200)
        
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(self.recipient_json['id'])),
                  json={'status': 'User present', 'user':self.sender_json}, status=200)

        response = app.post('/messages', json = new_message_with_attachment_data)
        self.assertEqual(response.status_code, 500)
        
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(self.recipient_json['email'])),
                  json={'status': 'User present', 'user':self.sender_json}, status=200)

        response = app.post('/messages', json = new_message_with_attachment_data)
        self.assertEqual(response.status_code, 201)

        response = app.post('/messages', json = new_message_without_attachment_data)
        self.assertEqual(response.status_code, 201)

    @responses.activate
    def test_02_retrieve_message_attachment(self):
        
        app = tested_app.test_client()

        # 500 users ms not available
        response = app.get('/messages/pending/5/attachment', json = {'requester_id':self.sender_json['id']})
        self.assertEqual(response.status_code, 500)

        
        # mocking users
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(self.sender_json['id'])),
                  json={'status': 'Current user is present',
                        'user': self.sender_json}, status=404)
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(self.recipient_json['id'])),
                  json={'status': 'Current user is present',
                        'user': self.recipient_json}, status=200)
                        
        # 404 user doesn't exist
        response = app.get('/messages/pending/5/attachment', json = {'requester_id':self.sender_json['id']})
        self.assertEqual(response.status_code, 404)

        # now the user exists
        responses.replace(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(self.sender_json['id'])),
                  json={'status': 'Current user is present',
                        'user': self.sender_json}, status=200)

        # 404 message not found
        response = app.get('/messages/pending/10000/attachment', json = {'requester_id':self.sender_json['id']})
        self.assertEqual(response.status_code, 404)

        # 403 forbidden not the sender
        response = app.get('/messages/pending/5/attachment', json = {'requester_id':self.recipient_json['id']})
        self.assertEqual(response.status_code, 403)

        # 404 attachment not found
        response = app.get('/messages/pending/6/attachment', json = {'requester_id':self.sender_json['id']})
        self.assertEqual(response.status_code, 404)

        # success
        response = app.get('/messages/pending/5/attachment', json = {'requester_id':self.sender_json['id']})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        assert '/9j/' in data['image']

        attachment_dir = os.path.join(basepath,str(5))
        os.remove(os.path.join(attachment_dir,'attachment.jpg'))
        os.rmdir(attachment_dir)

        # 500 failure: attachment not available
        response = app.get('/messages/pending/5/attachment', json = {'requester_id':self.sender_json['id']})
        self.assertEqual(response.status_code, 500)

    @responses.activate
    def test_03_delete_test_message_with_attachment(self):

        app = tested_app.test_client()

        # mocking users
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(self.sender_json['id'])),
                  json={'status': 'Current user is present',
                        'user': self.sender_json}, status=200)
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(self.recipient_json['id'])),
                  json={'status': 'Current user is present',
                        'user': self.recipient_json}, status=200)

        # mocking enough lottery points
        responses.add(responses.PUT, "%s/users/spend" % (USERS_ENDPOINT),
                  json={'status': 'Operation allowed'}, status=200)

        # success
        response = app.delete('/messages/pending/5', json = {'requester_id':self.sender_json['id']})
        self.assertEqual(response.status_code,200)

        # success
        response = app.delete('/messages/pending/6', json = {'requester_id':self.sender_json['id']})
        self.assertEqual(response.status_code,200)

    