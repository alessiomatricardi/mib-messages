import unittest
from mib import create_app
import responses
from mib import db
from flask_sqlalchemy import SQLAlchemy

class ResourcesTest(unittest.TestCase):

    @responses.activate
    def test_01_creating_messages(self):

        # creating an app instace to run test activities
        tested_app = create_app()
        USERS_ENDPOINT = tested_app.config['USERS_MS_URL']
        BLACKLIST_ENDPOINT = tested_app.config['BLACKLIST_MS_URL']
        REQUESTS_TIMEOUT_SECONDS = tested_app.config['REQUESTS_TIMEOUT_SECONDS']
        app = tested_app.test_client()

        # mocking variables
        json_sender_id = 1
        json_recipient_email = 'prova2@mail.com'
        json_recipient_id = 2
        new_message_data = {
            'requester_id': json_sender_id,
            'content' : 'testing!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [json_recipient_email],
            'image': '',
            'image_filename' : '',
            'is_draft': False
        }

        

        user2 = {
            'id' : json_recipient_id,
            'email' : 'prova2@mail.com',
            'firstname' : 'Maurizio',
            'lastname' : 'Costanzo',
            'date_of_birth' : '1938-08-28',
            'lottery_points' : 0,
            'has_picture' : False,
            'is_active' : True,
            'content_filter_enabled' : False
        }

        user3 = {
            'id': 3,
            'email': 'prova3@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }

        # unavailable users microservice
        response = app.post('/messages', json = new_message_data)
        self.assertEqual(response.status_code, 500)

        # mocking non existing user
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(3)),
                  json={'status': 'Current user not present'}, status=404)

        new_wrong_message_data = {
            'requester_id': 3,
            'content' : 'testing!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [json_recipient_email],
            'image': '',
            'image_filename' : '',
            'is_draft': False
        }

        response = app.post('/messages', json = new_wrong_message_data)
        self.assertEqual(response.status_code, 404)

        # mocking existing user but blacklist is unavailable
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(1)),
                  json={'status': 'Current user present'}, status=200)

        # unavailable blacklist microservice
        response = app.post('/messages', json = new_message_data)
        self.assertEqual(response.status_code, 500)

        # test unexisting recipient
        json_unexisting_recipient_email = 'prova5@mail.com'
        new_wrong_message_data = {
            'requester_id': 1,
            'content' : 'testing!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [json_unexisting_recipient_email],
            'image': '',
            'image_filename' : '',
            'is_draft': False
        }
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(json_unexisting_recipient_email)),
        json = {'status' : 'failure', 'message' : 'User not found'}, status=404)

        responses.add(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                json={
                    "blacklist": [3],
                    "description": "Blacklist successfully retrieved",
                    "status": "success"
                }, status=200)

        response = app.post('/messages', json = new_wrong_message_data)
        self.assertEqual(response.status_code, 404)

        # mocking existing user and blacklist available

        # this fails
        json_blocked_recipient_email = 'prova3@mail.com'
        new_wrong_message_data = {
            'requester_id': 1,
            'content' : 'testing!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [json_blocked_recipient_email],
            'image': '',
            'image_filename' : '',
            'is_draft': False
        }
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(json_blocked_recipient_email)),
                  json={'user': user3 }, status=200)

        responses.add(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                json={
                    "blacklist": [3],
                    "description": "Blacklist successfully retrieved",
                    "status": "success"
                }, status=200)

        response = app.post('/messages', json = new_wrong_message_data)
        self.assertEqual(response.status_code, 400)

        # this succeeds, PENDING message
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(json_recipient_email)),
                  json={'user': user2}, status=200)

        responses.add(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                json={
                    "blacklist": [3],
                    "description": "Blacklist successfully retrieved",
                    "status": "success"
                }, status=200)

        response = app.post('/messages', json = new_message_data)
        self.assertEqual(response.status_code, 201)

        # this succeeds, DRAFTS message
        new_draft_message_data = {
            'requester_id': json_sender_id,
            'content' : 'draft testing!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [json_recipient_email],
            'image': '',
            'image_filename' : '',
            'is_draft': True
        }
        response = app.post('/messages', json = new_draft_message_data)
        self.assertEqual(response.status_code, 201)

        # this succeeds, pending message which is going to be set as delivered
        new_draft_message_data = {
            'requester_id': json_sender_id,
            'content' : 'draft testing!',
            'deliver_time' : '2021-01-01 15:00',
            'recipients' : [json_recipient_email],
            'image': '',
            'image_filename' : '',
            'is_draft': False
        }
        response = app.post('/messages', json = new_draft_message_data)
        self.assertEqual(response.status_code, 201)

        with tested_app.app_context():
            from mib import db
            from mib.models import Message
            
            db.session.query(Message).filter(Message.id==3).update({'is_delivered':True})
            db.session.commit()
            
        # this succeeds, pending message with attached image
        new_message_data_image = {
            'requester_id': json_sender_id,
            'content' : 'testing!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [json_recipient_email],
            'image':'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',
            'image_filename' : 'attachment.jpg',
            'is_draft': False
        }
        response = app.post('/messages', json = new_message_data_image)
        self.assertEqual(response.status_code, 201)    

    @responses.activate
    def test_02_bottlebox(self):
        # creating an app instace to run test activities
        tested_app = create_app()
        USERS_ENDPOINT = tested_app.config['USERS_MS_URL']
        BLACKLIST_ENDPOINT = tested_app.config['BLACKLIST_MS_URL']
        app = tested_app.test_client()

        user1 = {
            'id' : 1,
            'email' : 'prova@mail.com',
            'firstname' : 'Maurizio',
            'lastname' : 'Costanzo',
            'date_of_birth' : '1938-08-28',
            'lottery_points' : 0,
            'has_picture' : False,
            'is_active' : True,
            'content_filter_enabled' : False
        }

        user2 = {
            'id': 2,
            'email': 'prova2@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }

        user3 = {
            'id': 3,
            'email': 'prova3@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }

        # failure without users response not already mocked, status_code 500
        response = app.get('/bottlebox/delivered', json = {'requester_id' : 1})
        self.assertEqual(response.status_code, 500)

        # failure without users response not already mocked, status_code 500
        response = app.get('/bottlebox/pending', json = {'requester_id' : 1})
        self.assertEqual(response.status_code, 500)

        # failure without users response not already mocked, status_code 500
        response = app.get('/bottlebox/received', json = {'requester_id' : 1})
        self.assertEqual(response.status_code, 500)

        # failure without users response not already mocked, status_code 500
        response = app.get('/bottlebox/drafts', json = {'requester_id' : 1})
        self.assertEqual(response.status_code, 500)

        # mocking
        # user 2 doesn't exist
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(2)),
                  json={'status': 'Current user not present'}, status=404)

        # user 1 exists
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(1)),
                  json={'status': 'Current user is present',
                        'user': user1}, status=200)

        # failure wrong label
        response = app.get('/bottlebox/not_a_label', json = {'requester_id' : 1})
        self.assertEqual(response.status_code,404)
        
        # DELIVERED BOTTLEBOX
        # failure user not found
        response = app.get('/bottlebox/delivered', json = {'requester_id' : 2})
        self.assertEqual(response.status_code, 404)

        # DRAFTS BOTTLEBOX
        # failure user not found
        response = app.get('/bottlebox/drafts', json = {'requester_id' : 2})
        self.assertEqual(response.status_code, 404)

        # RECEIVED BOTTLEBOX
        # failure user not found
        response = app.get('/bottlebox/received', json = {'requester_id' : 2})
        self.assertEqual(response.status_code, 404)

        # PENDING BOTTLEBOX
        # failure user not found
        response = app.get('/bottlebox/pending', json = {'requester_id' : 2})
        self.assertEqual(response.status_code, 404)

        # mock blacklist
        responses.add(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
        json={'blacklist': [40,45,56]}, status=200)

        # user 2 now exists
        responses.replace(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(2)),
                  json={'status': 'Current user is present',
                        'user': user2}, status=200)

        # DRAFTS BOTTLEBOX
        # success
        response = app.get('/bottlebox/drafts', json = {'requester_id' : 1})
        self.assertEqual(response.status_code,200)

        # PENDING BOTTLEBOX
        # success
        response = app.get('/bottlebox/pending', json = {'requester_id' : 1})
        self.assertEqual(response.status_code, 200)

        # DELIVERED BOTTLEBOX
        # success 
        response = app.get('/bottlebox/delivered', json = {'requester_id' : 1})
        self.assertEqual(response.status_code, 200)

        # RECEIVED BOTTLEBOX
        # success
        response = app.get('/bottlebox/received', json = {'requester_id' : 2})
        self.assertEqual(response.status_code,200) 

    @responses.activate
    def test_03_get_message_detail(self):
        # creating an app instace to run test activities
        tested_app = create_app()
        USERS_ENDPOINT = tested_app.config['USERS_MS_URL']
        BLACKLIST_ENDPOINT = tested_app.config['BLACKLIST_MS_URL']
        app = tested_app.test_client()

        user1 = {
            'id' : 1,
            'email' : 'prova@mail.com',
            'firstname' : 'Maurizio',
            'lastname' : 'Costanzo',
            'date_of_birth' : '1938-08-28',
            'lottery_points' : 0,
            'has_picture' : False,
            'is_active' : True,
            'content_filter_enabled' : False
        }

        user2 = {
            'id': 2,
            'email': 'prova2@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }

        user3 = {
            'id': 3,
            'email': 'prova3@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }

        # INTERNAL SERVER ERROR, users ms not available

        # failure 500 on get_pending
        response = app.get('/messages/pending/1', json = {'requester_id' : 1})
        self.assertEqual(response.status_code,500) 
        # failure 500 on get_delivered
        response = app.get('/messages/delivered/1', json = {'requester_id' : 1})
        self.assertEqual(response.status_code,500) 
        # failure 500 on get_received
        response = app.get('/messages/received/1', json = {'requester_id' : 1})
        self.assertEqual(response.status_code,500) 
        # failure 500 on get_draft
        response = app.get('/messages/drafts/1', json = {'requester_id' : 1})
        self.assertEqual(response.status_code,500) 

        # mocking users

        # users 1 and 2 exist
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(1)),
                  json={'status': 'Current user is present',
                        'user': user1}, status=200)

        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(2)),
                  json={'status': 'Current user is present',
                        'user': user2}, status=200)

        # users 3 doesn't exist
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(3)),
                  json={'status': 'Current user is not present',
                        'user': user3}, status=404)

        json_unexisting_requester={'requester_id':3}
        json_existing_requester={'requester_id':1}
        json_existing_requester_not_the_sender={'requester_id':2}

       # failure 404 on get_pending
        response = app.get('/messages/pending/1', json = json_unexisting_requester)
        self.assertEqual(response.status_code,404) 
        # failure 404 on get_delivered
        response = app.get('/messages/delivered/1', json = json_unexisting_requester)
        self.assertEqual(response.status_code,404) 
        # failure 404 on get_received
        response = app.get('/messages/received/1', json = json_unexisting_requester)
        self.assertEqual(response.status_code,404) 
        # failure 404 on get_draft
        response = app.get('/messages/drafts/1', json = json_unexisting_requester)
        self.assertEqual(response.status_code,404) 

        # failure on retrieving existing pending message having blacklist ms unavailable
        response = app.get('/messages/pending/1', json = json_existing_requester)
        self.assertEqual(response.status_code,500) 

        # failure on retrieving existing draft message having blacklist ms unavailable
        response = app.get('/messages/drafts/2', json = json_existing_requester)
        self.assertEqual(response.status_code,500) 

        # failure on retrieving existing delivered message having blacklist ms unavailable
        response = app.get('/messages/delivered/3', json = json_existing_requester)
        self.assertEqual(response.status_code,500) 

        # failure on retrieving existing draft message having blacklist ms unavailable
        response = app.get('/messages/received/3', json = json_existing_requester_not_the_sender)
        self.assertEqual(response.status_code,500) 

        # mocking blacklist
        responses.add(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
        json={'blacklist': [40,45,56]}, status=200)

        # failure on retrieving pending message having blacklist ms available but requester is not sender
        response = app.get('/messages/pending/1', json = json_existing_requester_not_the_sender)
        self.assertEqual(response.status_code,403) 

        # failure on retrieving draft message having blacklist ms available but requester is not sender
        response = app.get('/messages/drafts/2', json = json_existing_requester_not_the_sender)
        self.assertEqual(response.status_code,403) 

        # failure on retrieving delivered message having blacklist ms available but requester is not sender
        response = app.get('/messages/delivered/3', json = json_existing_requester_not_the_sender)
        self.assertEqual(response.status_code,403) 

        # failure on retrieving received message having blacklist ms available but requester is not recipient
        response = app.get('/messages/received/3', json = json_existing_requester)
        self.assertEqual(response.status_code,403) 

        # success on retrieving pending message having blacklist ms available
        response = app.get('/messages/pending/1', json = json_existing_requester)
        self.assertEqual(response.status_code,200) 

        # success on retrieving draft message having blacklist ms available
        response = app.get('/messages/drafts/2', json = json_existing_requester)
        self.assertEqual(response.status_code,200)
        
         # success on retrieving delivered message having blacklist ms available 
        response = app.get('/messages/delivered/3', json = json_existing_requester)
        self.assertEqual(response.status_code,200) 

        # success on retrieving received message having blacklist ms available 
        response = app.get('/messages/received/3', json = json_existing_requester_not_the_sender)
        self.assertEqual(response.status_code,200) 
        
    @responses.activate
    def test_04_modify_and_delete_draft_message(self):
        # creating an app instace to run test activities
        tested_app = create_app()
        USERS_ENDPOINT = tested_app.config['USERS_MS_URL']
        BLACKLIST_ENDPOINT = tested_app.config['BLACKLIST_MS_URL']
        app = tested_app.test_client()

        user1 = {
            'id' : 1,
            'email' : 'prova@mail.com',
            'firstname' : 'Maurizio',
            'lastname' : 'Costanzo',
            'date_of_birth' : '1938-08-28',
            'lottery_points' : 0,
            'has_picture' : False,
            'is_active' : True,
            'content_filter_enabled' : False
        }

        user2 = {
            'id': 2,
            'email': 'prova2@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }

        user3 = {
            'id': 3,
            'email': 'prova3@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }

        json_modify_draft = {
            'requester_id': user1['id'],
            'content' : 'testing!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [user2['email']],
            'image': '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',
            'image_filename' : 'attachment.jpg',
            'delete_image':False,
            'is_sent': False
        }
        json_modify_draft_image_replace = {
            'requester_id': user1['id'],
            'content' : 'testing!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [user2['email']],
            'image': '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',
            'image_filename' : 'replaced_attachment.jpg',
            'delete_image':False,
            'is_sent': False
        }
        json_modify_draft_wrong_requester = {
            'requester_id': user2['id'],
            'content' : 'testing!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [user2['email']],
            'image': '',
            'image_filename' : '',
            'delete_image': False,
            'is_sent': False
        }
        json_modify_draft_unexisting_requester = {
            'requester_id': user3['id'],
            'content' : 'testing!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [user2['email']],
            'image': '',
            'image_filename' : '',
            'delete_image':False,
            'is_sent': False
        }
        json_delete_draft_unexisting_requester = {'requester_id' : 3}
        json_delete_draft_wrong_requester = {'requester_id' : 2}
        json_delete_draft = {'requester_id' : 1}
        
        # INTERNAL SERVER ERROR, users ms not available
 
        # failure 500 on updating
        response = app.put('/messages/drafts/2', json = json_modify_draft)
        self.assertEqual(response.status_code,500)

        # failure 500 on deleting
        response = app.delete('/messages/drafts/2', json = json_delete_draft)
        self.assertEqual(response.status_code,500)

        # mocking users
        # users 1 and 2 exist
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(1)),
                  json={'status': 'Current user is present',
                        'user': user1}, status=200)

        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(2)),
                  json={'status': 'Current user is present',
                        'user': user2}, status=200)

        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(user2['email'])),
                  json={'status': 'Current user is present',
                        'user': user2}, status=200)

        # users 3 doesn't exist
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(3)),
                  json={'status': 'Current user is not present',
                        'user': user3}, status=404) 
        
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(user3['email'])), 
        status=404)

        # failure 404 on updating
        response = app.put('/messages/drafts/2', json = json_modify_draft_unexisting_requester)
        self.assertEqual(response.status_code,404)

        # failure 404 on deleting
        response = app.delete('/messages/drafts/2', json = json_delete_draft_unexisting_requester)
        self.assertEqual(response.status_code,404)

        # failure 403 on updating when the user is not the sender of draft
        response = app.put('/messages/drafts/2', json = json_modify_draft_wrong_requester)
        self.assertEqual(response.status_code,403)

        # failure 403 on deleting when the user is not the sender of draft
        response = app.delete('/messages/drafts/2', json = json_delete_draft_wrong_requester)
        self.assertEqual(response.status_code,403)

        # failure 500 without having blacklist ms available
        response = app.put('/messages/drafts/2', json = json_modify_draft)
        self.assertEqual(response.status_code,500)

        # mocking blacklist
        responses.add(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
        json={'blacklist': [40,45,56], "description": "Blacklist successfully retrieved",
                    "status": "success"}, status=200)
               
        # failure 404 on updating a non existing draft message
        response = app.put('/messages/drafts/10000', json = json_modify_draft)
        self.assertEqual(response.status_code,404)
        
        # success on updating n.1
        response = app.put('/messages/drafts/2', json = json_modify_draft)
        self.assertEqual(response.status_code,200)

        # success on updating n.2
        response = app.put('/messages/drafts/2', json = json_modify_draft_image_replace)
        self.assertEqual(response.status_code,200)

        json_modify_draft = {
            'requester_id': user1['id'],
            'content' : 'testing!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [user3['email']],
            'image': '',
            'image_filename' : '',
            'delete_image':False,
            'is_sent': False
        }

        responses.replace(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(user3['email'])), 
            json = {'status' : 'User not found'}, status=404)

        # failure 404 not found recipient
        response = app.put('/messages/drafts/2', json = json_modify_draft)
        self.assertEqual(response.status_code,404)

        # success on update with a new recipient
        user4 = {
            'id': 4,
            'email': 'prova4@mail.com',
            'firstname': 'Piersilvio',
            'lastname': 'Berlusconi',
            'date_of_birth': '1969-04-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }
        
        json_modify_draft = {
            'requester_id': user1['id'],
            'content' : 'two recipient update test!',
            'deliver_time' : '2025-01-01 15:00',
            'recipients' : [user2['email'], user4['email']],
            'image': '',
            'image_filename' : '',
            'delete_image':True,
            'is_sent': False
        }


        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(4)),
                  json={'status': 'Current user is present',
                        'user': user4}, status=200)

        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(user4['email'])),
                  json={'status': 'Current user is present',
                        'user': user4}, status=200)

        # success on updating n.3, testing multiple recipients and removing attached image
        response = app.put('/messages/drafts/2', json = json_modify_draft)
        self.assertEqual(response.status_code,200)

        # now user 4 is in the blacklist
        # mocking blacklist
        responses.replace(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
        json={'blacklist': [4,40,45,56], "description": "Blacklist successfully retrieved",
                    "status": "success"}, status=200)

        # success on updating n.3, user4 is still a selected recipient, but is going to be removed because inside blacklist
        response = app.put('/messages/drafts/2', json = json_modify_draft)
        self.assertEqual(response.status_code,200)

        # draft deletion json variables
        json_delete_draft_existing_requester = {'requester_id':1}
        json_delete_draft_existing_requester_not_the_sender = {'requester_id':2}
        
        # delete draft failure 404, draft not found
        response = app.delete('/messages/drafts/100', json = json_delete_draft_existing_requester)
        self.assertEqual(response.status_code,404)

        # delete draft failure 403, requester id is not the sender id
        response = app.delete('/messages/drafts/2', json = json_delete_draft_existing_requester_not_the_sender)
        self.assertEqual(response.status_code,403)

        # success
        response = app.delete('/messages/drafts/2', json = json_delete_draft_existing_requester)
        self.assertEqual(response.status_code,200)

    @responses.activate
    def test_05_delete_pending_message(self):
        # creating an app instace to run test activities
        tested_app = create_app()
        USERS_ENDPOINT = tested_app.config['USERS_MS_URL']
        BLACKLIST_ENDPOINT = tested_app.config['BLACKLIST_MS_URL']
        app = tested_app.test_client()

        user1 = {
            'id' : 1,
            'email' : 'prova@mail.com',
            'firstname' : 'Maurizio',
            'lastname' : 'Costanzo',
            'date_of_birth' : '1938-08-28',
            'lottery_points' : 100,  # the user needs lottery points to delete a pending message
            'has_picture' : False,
            'is_active' : True,
            'content_filter_enabled' : False
        }

        user2 = {
            'id': 2,
            'email': 'prova2@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }

        user3 = {
            'id': 3,
            'email': 'prova3@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }
        # pending message deletion variables
        json_delete_pending_existing_requester = {'requester_id':1}
        json_delete_pending_unexisting_requester = {'requester_id':3}
        json_delete_pending_not_the_sender = {'requester_id':2}

        # 500 unavailable users
        response = app.delete('/messages/pending/1', json = json_delete_pending_existing_requester)
        self.assertEqual(response.status_code,500)

        # mocking users
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(1)),
                  json={'status': 'Current user is present',
                        'user': user1}, status=200)
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(2)),
                  json={'status': 'Current user is present',
                        'user': user2}, status=200)
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(3)),
                  json={'status': 'Current user is not present',
                        'user': user3}, status=404)

        # 404 pending message not found
        response = app.delete('/messages/pending/100', json = json_delete_pending_existing_requester)
        self.assertEqual(response.status_code,404)

        # 403 not the sender
        response = app.delete('/messages/pending/1', json = json_delete_pending_not_the_sender)
        self.assertEqual(response.status_code,403)

        # 404 non existing user
        response = app.delete('/messages/pending/1', json = json_delete_pending_unexisting_requester)
        self.assertEqual(response.status_code,404)

        # mocking not enough lottery points
        responses.add(responses.PUT, "%s/users/spend" % (USERS_ENDPOINT),
                  json={'status': 'Not enough lottery points'}, status=403)

        # not enough lottery points
        response = app.delete('/messages/pending/1', json = json_delete_pending_existing_requester)
        self.assertEqual(response.status_code,403)

        # mocking enough lottery points
        responses.replace(responses.PUT, "%s/users/spend" % (USERS_ENDPOINT),
                  json={'status': 'Operation allowed'}, status=200)

        # success
        response = app.delete('/messages/pending/4', json = json_delete_pending_existing_requester)
        self.assertEqual(response.status_code,200)

    @responses.activate
    def test_06_report_received_message(self):
        # creating an app instace to run test activities
        tested_app = create_app()
        USERS_ENDPOINT = tested_app.config['USERS_MS_URL']
        BLACKLIST_ENDPOINT = tested_app.config['BLACKLIST_MS_URL']
        app = tested_app.test_client()

        user1 = {
            'id' : 1,
            'email' : 'prova@mail.com',
            'firstname' : 'Maurizio',
            'lastname' : 'Costanzo',
            'date_of_birth' : '1938-08-28',
            'lottery_points' : 0,
            'has_picture' : False,
            'is_active' : True,
            'content_filter_enabled' : False
        }

        user2 = {
            'id': 2,
            'email': 'prova2@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }

        user3 = {
            'id': 3,
            'email': 'prova3@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }

        # json variables
        json_recipient_requester = {'requester_id':user2['id']}
        json_not_recipient_requester = {'requester_id':user1['id']}
        json_unexisting_recipient_requester = {'requester_id':user3['id']}

        # 500
        response = app.put('/messages/received/3/report', json = json_recipient_requester)
        self.assertEqual(response.status_code,500)
        
        # mocking user
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(1)),
                  json={'status': 'Current user is present',
                        'user': user1}, status=200)
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(2)),
                  json={'status': 'Current user is present',
                        'user': user2}, status=200)
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(3)),
                  json={'status': 'Current user is not present',
                        'user': user3}, status=404)

        # 404 not existing user
        response = app.put('/messages/received/3/report', json = json_unexisting_recipient_requester)
        self.assertEqual(response.status_code,404)

        # 403 not recipient
        response = app.put('/messages/received/3/report', json = json_not_recipient_requester)
        self.assertEqual(response.status_code,403)

        # mocking blacklist ??

        # success report
        response = app.put('/messages/received/3/report', json = json_recipient_requester)
        self.assertEqual(response.status_code,200)

        # 403 in reporting again
        response = app.put('/messages/received/3/report', json = json_recipient_requester)
        self.assertEqual(response.status_code,403)

    @responses.activate
    def test_07_hide_received_message(self):
        # creating an app instace to run test activities
        tested_app = create_app()
        USERS_ENDPOINT = tested_app.config['USERS_MS_URL']
        BLACKLIST_ENDPOINT = tested_app.config['BLACKLIST_MS_URL']
        app = tested_app.test_client()

        user1 = {
            'id' : 1,
            'email' : 'prova@mail.com',
            'firstname' : 'Maurizio',
            'lastname' : 'Costanzo',
            'date_of_birth' : '1938-08-28',
            'lottery_points' : 0,
            'has_picture' : False,
            'is_active' : True,
            'content_filter_enabled' : False
        }

        user2 = {
            'id': 2,
            'email': 'prova2@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }

        user3 = {
            'id': 3,
            'email': 'prova3@mail.com',
            'firstname': 'Maurizio',
            'lastname': 'Costanzo',
            'date_of_birth': '1938-08-28',
            'lottery_points': 0,
            'has_picture': False,
            'is_active': True,
            'content_filter_enabled': False
        }

        # json variables
        json_recipient_requester = {'requester_id':user2['id']}
        json_not_recipient_requester = {'requester_id':user1['id']}
        json_unexisting_recipient_requester = {'requester_id':user3['id']}

        # 500
        response = app.put('/messages/received/3/hide', json = json_recipient_requester)
        self.assertEqual(response.status_code,500)
        
        # mocking user
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(1)),
                  json={'status': 'Current user is present',
                        'user': user1}, status=200)
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(2)),
                  json={'status': 'Current user is present',
                        'user': user2}, status=200)
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(3)),
                  json={'status': 'Current user is not present',
                        'user': user3}, status=404)

        # 404 not existing user
        response = app.put('/messages/received/3/hide', json = json_unexisting_recipient_requester)
        self.assertEqual(response.status_code,404)

        # 403 not recipient
        response = app.put('/messages/received/3/hide', json = json_not_recipient_requester)
        self.assertEqual(response.status_code,403)

        # mocking blacklist ??

        # success report
        response = app.put('/messages/received/3/hide', json = json_recipient_requester)
        self.assertEqual(response.status_code,200)

        # 403 in reporting again
        response = app.put('/messages/received/3/hide', json = json_recipient_requester)
        self.assertEqual(response.status_code,403)
