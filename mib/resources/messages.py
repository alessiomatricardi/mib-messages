from flask import request
from mib.dao.message_manager import MessageManager
from mib.dao.report_manager import ReportManager
from flask import jsonify
import requests
from mib import app
from mib.emails import send_email
from mib.content_filter import censure_content


USERS_ENDPOINT = app.config['USERS_MS_URL']
BLACKLIST_ENDPOINT = app.config['BLACKLIST_MS_URL']
REQUESTS_TIMEOUT_SECONDS = app.config['REQUESTS_TIMEOUT_SECONDS']

RECEIVED_LABEL = 'received'
DRAFT_LABEL = 'drafts'
PENDING_LABEL = 'pending'
DELIVERED_LABEL = 'delivered'

'''
TODO AGGIUNGERE GESTORE RICHIESTE VERSO ALTRI MICROSERVIZI PER MIGLIORARE LEGGIBILITA` CODICE
'''


"""
TODO DA MODIFICARE IN BASE ALLA LABEL
"""
def get_bottlebox(label):

    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # check if the user_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:
            response_object = {
                'status': 'failure',
                'description': 'Error in retrieving user',
            }
            return response.json(), response.status_code

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500

    # retrieve messages of the requested label for the specified user
    messages = MessageManager.retrieve_messages_by_label(label, requester_id)

    # check if the requested label is correct
    if messages is None:
        response_object = {
            'status': 'failure',
            'description': 'Bad request: Label is wrong',
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
        'description': 'Bottlebox retrieved',
        'messages': messages_json
    }

    return jsonify(response_object), 200


def get_received_message(message_id):

    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # check if the message exists
    message = MessageManager.retrieve_message_by_id(RECEIVED_LABEL, message_id)
    if not message:
        response_object = {
            'status' : 'failure',
            'description' : 'Message not found'
        }
        return jsonify(response_object), 404

    # check if the user_id is a recipient of the message
    message_recipient = MessageManager.retrieve_message_recipient(message_id, requester_id)
    if not message_recipient:
        response_object = {
            'status' : 'failure',
            'description' : 'Forbidden: user is not a recipient of this message'
        }
        return jsonify(response_object), 403

    # get sender informations
    sender = None

    try:
        data = {'requester_id': message.sender_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(message.sender_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:
            return response.json(), response.status_code

        sender = response.json()['user']

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):

        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving the sender',
        }
        return jsonify(response_object), 500
    

    # check if the message is already read. If not, set it as read and send a notification to the sender
    if not message_recipient.is_read:

        MessageManager.set_message_as_read(message_recipient)

        # TODO interazione con user per ricavare il nome dell'utente recipient
        email_message = "Subject: Message notification\n\nThe message you sent to " + "PEPPINO" + " has been read."


        email = sender['email']

        send_email(email, email_message)

    # check if the sender is in our blacklist, in order to don't permit to see his profile
    # TODO INTERAZIONE CON BLACKLIST
    '''
    other_id = detailed_message.sender_id

    # checking if the message is from a blocked or blocking user
    blacklist_istance = bottlebox_logic.user_blacklist_status(other_id,current_user.id)

    # blocked variable is passed to render_template in order to display or not the reply and block buttons
    if not blacklist_istance:
        blocked = False
    else:
        blocked = True
    '''
    is_sender_in_blacklist = True
    

    message_json = message.serialize()

    # store info of the sender
    message_json['sender_firstname'] = sender['firstname']
    message_json['sender_lastname'] = sender['lastname']
    message_json['sender_email'] = sender['email']

    # store that the sender is into blacklist or not
    message_json['is_sender_in_blacklist'] = is_sender_in_blacklist

    # store that the message is read or not
    message_json['is_read'] = message_recipient.is_read

    # censure the message if the user has content filter enabled
    content_filter_enabled = False

    # TODO implementare in user /users/id/content_filter
    '''
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s/content_filter" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:
            return response.json(), response.status_code

        content_filter_enabled = response.json()['enabled']

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):

        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving the sender',
        }
        return jsonify(response_object), 500
    '''
    if content_filter_enabled:
        censored_content = censure_content(message.content)
        message_json['content'] = censored_content

    # check if the user already reported this message
    reported = ReportManager.is_message_reported(message_id, requester_id)
    message_json['is_reported'] = reported

    response_object = {
        'status' : 'success',
        'description' : 'Message retrieved',
        'message' : message_json
    }
    return jsonify(response_object), 200


def get_draft_message(message_id):

    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # retrieving the message, if exists
    message = MessageManager.retrieve_message_by_id(DRAFT_LABEL, message_id)

    if not message:
        response_object = {
            'status' : 'failure',
            'description' : 'Message not found'
        }
        return jsonify(response_object), 404

    # check if the user_id is the sender of the message
    if message.sender_id != requester_id:
        response_object = {
            'status' : 'failure',
            'description' : 'Forbidden: user is not the sender of this message'
        }
        return jsonify(response_object), 403

    recipients = MessageManager.retrieve_message_recipients(message_id)

    # API gateway will use this field to render the form
    recipient_emails = ['a.matricardi@studenti.unipi.it']

    # checks that already saved recipients are still available (they could have become inactive or blocked/blocking user)
    for recipient in recipients:
        # TODO CHIEDI A USER SE UTENTE DISPONIBILE
        # TODO CHIEDI A BLACKLIST SE UTENTE BLOCCATO/BLOCCANTE
        user = dict()
        user['is_active'] = True
        user['email'] = 'prova@example.com'

        if not user['is_active']: #'''or user is in blacklist'''
            # remove user from recipients
            MessageManager.remove_message_recipient(message_id, 123)
        else:
            recipient_emails.append(user['email'])


    message_json = message.serialize()

    # store recipients
    message_json['recipients'] = recipient_emails

    response_object = {
        'status' : 'success',
        'description' : 'Message retrieved',
        'message' : message_json
    }
    return jsonify(response_object), 200


def get_pending_message(message_id):

    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # retrieving the message, if exists
    message = MessageManager.retrieve_message_by_id(PENDING_LABEL, message_id)

    # since pending and delivered messages are similar, the share most of the code
    return get_pending_or_delivered_message(message, requester_id)


def get_delivered_message(message_id):

    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # retrieving the message, if exists
    message = MessageManager.retrieve_message_by_id(DELIVERED_LABEL, message_id)

    # since pending and delivered messages are similar, the share most of the code
    return get_pending_or_delivered_message(message, requester_id)


def get_pending_or_delivered_message(message, requester_id):
    
    if not message:
        response_object = {
            'status' : 'failure',
            'description' : 'Message not found'
        }
        return jsonify(response_object), 404

    # check if the user_id is the sender of the message
    if message.sender_id != requester_id:
        response_object = {
            'status' : 'failure',
            'description' : 'Forbidden: user is not the sender of this message'
        }
        return jsonify(response_object), 403

    # TODO INVESTIGATE
    # checks if a recipient has blocked the current_user or has been blocked
    '''
    for i in range(len(recipients)):
        other_id = recipients[i].id

        blacklist_istance = bottlebox_logic.user_blacklist_status(other_id,current_user.id)

        # appends to blocked_info a tuple to link the respective recipient and its blacklist status
        if not blacklist_istance:
            blocked_info.append([recipients[i], False])
        else:
            blocked_info.append([recipients[i], True])
    '''

    # retrieve sender info

    sender = None

    try:
        auth_data = {'requester_id': message.sender_id}
        response = requests.get("%s/users/%s" %
                                (USERS_ENDPOINT, str(message.sender_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=auth_data)

        if response.status_code != 200:
            return response.json(), response.status_code

        sender = response.json()['user']

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):

        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500

    recipients = MessageManager.retrieve_message_recipients(message.id)

    recipients_list = []
    user = dict()
    user['email'] = 'a.matricardi@studenti.unipi.it'
    user['id'] = 1
    user['firstname'] = 'Alessio'
    user['lastname'] = 'Matricardi'
    user['available'] = False

    # checks that already saved recipients are still available (they could have become inactive or blocked/blocking user)
    for recipient in recipients:
        # TODO CHIEDI A USER di darti utente
        # TODO CHIEDI A BLACKLIST SE UTENTE BLOCCATO/BLOCCANTE
        recipients_list.append(user)


    message_json = message.serialize()

    # store recipients
    message_json['recipients'] = recipients_list

    # censure the message if the user has content filter enabled
    if sender['content_filter_enabled']:
        censored_content = censure_content(message.content)
        message_json['content'] = censored_content

    response_object = {
        'status' : 'success',
        'description' : 'Message retrieved',
        'message' : message_json
    }
    return jsonify(response_object), 200


# POST /hide/<message_id>/<user_id>
def hide_message():

    # TODO L'API gateway valida il form e passa i parametri user_id e message_id (SEE CODE BELOW)
    """
    form = HideForm()

    if not form.validate_on_submit():
        abort(400)

    message_id = 0
    try:
        # retrieve the message id from the form
        message_id = int(form.message_id.data)
    except:
        abort(400)
    """
    # get info about the requester and the message
    data = request.get_json()
    requester_id = data.get('requester_id')
    message_id = data.get('message_id')

    message_recipient = MessageManager.retrieve_message_recipient(message_id, requester_id)

    if message_recipient is None: 
        response_object = {
            'status' : 'failure',
            'description' : 'Forbidden: user is not a recipient of this message'
        }
        return jsonify(response_object), 403

    if message_recipient.is_hide:
        response_object = {
            'status' : 'failure',
            'description' : 'Forbidden: user not allowed'
        }
        return jsonify(response_object), 403

    MessageManager.hide_message(message_recipient)

    response_object = {
        'status' : 'success',
        'description' : 'Message successfully deleted'
    }
    return jsonify(response_object), 200
