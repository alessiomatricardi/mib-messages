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
            'image': '',
            'image_filename' : '',
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
               
        # success on updating n.1
        response = app.put('/messages/drafts/2', json = json_modify_draft)
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
            'delete_image':False,
            'is_sent': False
        }


        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(4)),
                  json={'status': 'Current user is present',
                        'user': user4}, status=200)

        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(user4['email'])),
                  json={'status': 'Current user is present',
                        'user': user4}, status=200)

        # success on updating n.2
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
        response = app.delete('/messages/pending/1', json = json_delete_pending_existing_requester)
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
