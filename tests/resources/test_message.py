import unittest
from mib import create_app
import responses



class ResourcesTest(unittest.TestCase):

    @responses.activate
    def test_01_creating_messages(self):
        pass

    @responses.activate
    def test_02_bottlebox(self):
        # creating an app instace to run test activities
        tested_app = create_app()
        USERS_ENDPOINT = tested_app.config['USERS_MS_URL']
        app = tested_app.test_client()

        '''
        # failure without users response not already mocked, status_code 500
        # TODO affinchè funzioni prima inserire un messaggio casuale
        response = app.get('/bottlebox/delivered', json = {'requester_id' : 1})
        self.assertEqual(response.status_code, 500)


        # mocking
        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(2)),
                  json={'status': 'Current user not present'}, status=404)

        responses.add(responses.GET, "%s/users/%s" % (USERS_ENDPOINT, str(1)),
                  json={'status': 'Current user is present'}, status=200)

        # falure user not found
        response = app.get('/bottlebox/delivered', json = {'requester_id' : 2})
        self.assertEqual(response.status_code, 500)
        '''

        # failure wrong label
        response = app.get('/bottlebox/not_a_label', json = {'requester_id' : 1})
        self.assertEqual(response.status_code,404)

        # retrieving received messages bottlebox
        response = app.get('/bottlebox/received', json = {'requester_id' : 1})
        self.assertEqual(response.status_code,200)

        # retrieving delivered messages bottlebox
        response = app.get('/bottlebox/drafts', json={'requester_id': 1})
        self.assertEqual(response.status_code, 200)

        # retrieving delivered messages bottlebox
        response = app.get('/bottlebox/pending', json={'requester_id': 1})
        self.assertEqual(response.status_code, 200)

        # retrieving delivered messages bottlebox
        response = app.get('/bottlebox/delivered', json = {'requester_id' : 1})
        self.assertEqual(response.status_code,200)

        pass