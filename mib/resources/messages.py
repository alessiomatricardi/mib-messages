from mib.dao.message_manager import MessageManager
from flask import jsonify
import requests
from mib import app


USERS_ENDPOINT = app.config['USERS_MS_URL']
REQUESTS_TIMEOUT_SECONDS = app.config['REQUESTS_TIMEOUT_SECONDS']


def get_bottlebox(user_id, label):

    # check if the user_id exists
    try:
        response = requests.get("%s/users/%s/list/%s" % (USERS_ENDPOINT, str(user_id), str(user_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS)
        
        if response.status_code != 200:
            response_object = {
                'status': 'failure',
                'message': 'Error in retrieving user',
            }
            return response.json(), response.status_code
            
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'message': 'Error in retrieving user',
        }
        return jsonify(response_object), 500

    # retrieve messages of the requested label for the specified user
    messages = MessageManager.retrieve_messages_by_label(label, user_id)

    # check if the requested label is correct
    if messages is None:
        response_object = {
            'status': 'failure',
            'message': 'Bad request: Label is wrong',
        }
        return jsonify(response_object), 400

    messages_json = []
    if label == 'received':
        # received messages needs is_read field in order to inform the recipient about unread messages
        for message in messages:
            message_det = message[0].serialize()
            message_det['is_read'] = message[1]
            messages_json.append(message_det)
    else:
        # other messages needs recipients list
        for message in messages:
            message_det = message.serialize()
            message_det['recipients'] = MessageManager.retrieve_message_recipients(message.id)
            messages_json.append(message_det)

    response_object = {
        'status': 'success',
        'message': 'Bottlebox retrieved',
        'message_list': messages_json
    }

    return jsonify(response_object), 200