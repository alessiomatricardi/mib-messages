import unittest
from mib import create_app
import responses



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
            'is_draft': False
        }

        user2 = {
            'id' : 2,
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
            'is_draft': False
        }

        response = app.post('/messages', json = new_wrong_message_data)
        self.assertEqual(response.status_code, 404)

        # mocking existing user but blacklist is unavailable
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(1)),
                  json={'status': 'Current user not present'}, status=200)

        # unavailable blacklist microservice
        response = app.post('/messages', json = new_message_data)
        self.assertEqual(response.status_code, 500)

        # test unexisting recipient
        json_unexisting_recipient_email = 'prova5@mail.com'
        new_wrong_message_data = {'requester_id': 1,
                             'content' : 'testing!',
                             'deliver_time' : '2025-01-01 15:00',
                             'recipients' : [json_unexisting_recipient_email],
                             'image': '',
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

        # this succeeds
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

        # success
        response = app.get('/bottlebox/delivered', json = {'requester_id' : 1})
        self.assertEqual(response.status_code, 200)

        # RECEIVED BOTTLEBOX
        # failure user not found
        response = app.get('/bottlebox/received', json = {'requester_id' : 2})
        self.assertEqual(response.status_code, 404)

        # success
        response = app.get('/bottlebox/received', json = {'requester_id' : 1})
        self.assertEqual(response.status_code,200)

        # DRAFTS BOTTLEBOX
        # failure user not found
        response = app.get('/bottlebox/drafts', json = {'requester_id' : 2})
        self.assertEqual(response.status_code, 404)

        # success
        response = app.get('/bottlebox/drafts', json = {'requester_id' : 1})
        self.assertEqual(response.status_code,200)

        # PENDING BOTTLEBOX
        # failure user not found
        response = app.get('/bottlebox/pending', json = {'requester_id' : 2})
        self.assertEqual(response.status_code, 404)

        # user 2 now exists
        responses.replace(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(2)),
                  json={'status': 'Current user is present',
                        'user': user2}, status=200)

        # mock blacklist
        responses.add(responses.GET, "%s/blacklist" % (BLACKLIST_ENDPOINT),
                  json={'blacklist': [40,45,56]}, status=200)

        # success
        response = app.get('/bottlebox/pending', json = {'requester_id' : 1})
        self.assertEqual(response.status_code, 200)
