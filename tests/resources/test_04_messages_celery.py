from mib.background import deliver_message_and_send_notification
import unittest
from mib import create_app
import responses

tested_app = create_app()

USERS_ENDPOINT = tested_app.config['USERS_MS_URL']
BLACKLIST_ENDPOINT = tested_app.config['BLACKLIST_MS_URL']

class CeleryTest(unittest.TestCase):

    @responses.activate
    def test_task(self):

        task = deliver_message_and_send_notification.apply()
        self.assertEqual(task.result,'No notifications have to be sent')