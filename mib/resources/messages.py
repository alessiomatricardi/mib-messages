from flask import request
from mib.dao.message_manager import MessageManager
from mib.dao.report_manager import ReportManager
from flask import jsonify
import requests
from mib import app
from mib.models import Message, Message_Recipient, Report
import datetime
import os
from mib.logic.message_logic import MessageLogic
from mib.logic.user import User


USERS_ENDPOINT = app.config['USERS_MS_URL']
BLACKLIST_ENDPOINT = app.config['BLACKLIST_MS_URL']
REQUESTS_TIMEOUT_SECONDS = app.config['REQUESTS_TIMEOUT_SECONDS']

RECEIVED_LABEL = 'received'
DRAFT_LABEL = 'drafts'
PENDING_LABEL = 'pending'
DELIVERED_LABEL = 'delivered'


# CREATE OPERATIONS


def new_message():
    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')
    content = data.get('content')
    deliver_time = data.get('deliver_time')
    recipients = data.get('recipients')
    img_base64 = data.get('image') # TODO VALUTARE DI INVIARE NEL CAMPO "FILES" ???
    # TODO SEMPRE IMMAGINE: SE FORNITO JSON, VA FORNITO ANCHE IL FORMATO DELL'IMMAGINE (.JPG, .PNG, ....)
    is_draft = data.get('is_draft')

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:

            return response.json(), response.status_code

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500

    blacklist = []

    # retrieve blacklist
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/blacklist" % (BLACKLIST_ENDPOINT),
                                    timeout=REQUESTS_TIMEOUT_SECONDS,
                                    json=data)
        if response.status_code != 200:

            return response.json(), response.status_code
        
        blacklist = response.json()['blacklist']

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving blacklist',
        }
        return jsonify(response_object), 500

    valid_recipient_ids = []

    # checks on recipients
    for recipient_email in recipients:

        # checking recipient availability
        try:

            # checking that the recipient's email corresponds to an existing user
            response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(recipient_email)),
                                    timeout=REQUESTS_TIMEOUT_SECONDS)

            if response.status_code != 200:

                return response.json(), response.status_code

            # retrieve user data
            recipient_json = response.json()['user']
            recipient = User.build_from_json(recipient_json)

            # checking that the retrieved user corresponds to an available one
            # if not, skip him
            if not recipient.is_active or recipient.id in blacklist:
                continue
            
            # the current recipient user passed all checks
            valid_recipient_ids.append(recipient.id)

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            response_object = {
                'status': 'failure',
                'description': 'Error in retrieving user',
            }
            return jsonify(response_object), 500
    
    # if the message has no recipients, return with an error
    if len(valid_recipient_ids) == 0:
        response_object = {
            'status' : 'failure',
            'description' : 'Message has no valid recipients'
        }
        return jsonify(response_object), 400


    # creating message after passing all checks
    message = Message()
    message.sender_id = requester_id
    message.content = content
    message.deliver_time = datetime.datetime.fromisoformat(deliver_time)
    message.image = img_base64  #TODO VALUTARE SE FARLO DIVENTARE BOOLEANO
    if not is_draft:
        # save message as pending
        message.is_sent = True

    MessageManager.create_message(message)

    # creating the respective message recipients
    for recipient_id in valid_recipient_ids:
        # creating message recipient instance
        message_recipient = Message_Recipient()

        message_recipient.id = message.id
        message_recipient.is_read = False               # redundant because the db automatically set it to False
        message_recipient.recipient_id = recipient_id

        MessageManager.create_message_recipient(message_recipient)

    # TODO IMPORTANTE!!!!!!!!!
    # CARTELLA ATTACHMENTS GIA' CREATA IN __INIT__.PY

    if img_base64 != '':
        # create a subdirectory of 'attachments' having as name the id of the message
        os.mkdir(os.path.join(os.getcwd(), 'mib', 'static', 'attachments', str(id)))

        # TODO save attachment
        
        # decoding image
        #img_data = BytesIO(base64.b64decode(img_base64))

        # store it, in case of a previously inserted image it's going to be overwritten
        try:

            #img = Image.open(img_data)
            path_to_save = os.path.join(os.getcwd(), 'mib', 'static', 'attachments',
                                    str(id), 'attachment' + '.png')
            #img.save(path_to_save, "JPEG", quality=100, subsampling=0)

        except Exception:
            response_object = {
                'status': 'failure',
                'description': 'Error in saving the image',
            }
            return jsonify(response_object), 500

    response_object = {
        'status': 'success',
        'description': 'Message created',
    }
    return jsonify(response_object), 201


# READ OPERATIONS


def get_received_bottlebox():
    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:

            return response.json(), response.status_code

        # build user object from json
        requester_json = response.json()['user']
        requester = User.build_from_json(requester_json)

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500


    # retrieve messages of the requested label for the specified user
    messages = MessageManager.retrieve_messages_by_label(RECEIVED_LABEL, requester_id)

    messages_json = []

    for message in messages:
        # get all information we need
        message_json, status_code = MessageLogic.get_received_message(message, requester)

        # check status code
        if status_code == 200:
            messages_json.append(message_json)
        else:
            if status_code == 403:
                response_object = {
                    'status': 'failure',
                    'description': 'Forbidden: user is not a recipient of this message'
                }
            elif status_code == 404:
                response_object = {
                    'status': 'failure',
                    'description': 'Message not found'
                }
            elif status_code == 500:
                response_object = {
                    'status': 'failure',
                    'description': 'Server error: Error in retrieving sender/blacklist',
                }

            return jsonify(response_object), status_code


    response_object = {
        'status': 'success',
        'description': 'Bottlebox retrieved',
        'messages': messages_json
    }

    return jsonify(response_object), 200


def get_draft_bottlebox():
    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:

            return response.json(), response.status_code

        # build user object from json
        requester_json = response.json()['user']
        requester = User.build_from_json(requester_json)

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500


    # retrieve messages of the requested label for the specified user
    messages = MessageManager.retrieve_messages_by_label(DRAFT_LABEL, requester_id)

    messages_json = []

    for message in messages:
        # get all information we need
        message_json, status_code = MessageLogic.get_draft_message(message, requester)

        # check status code
        if status_code == 200:
            messages_json.append(message_json)
        else:
            if status_code == 403:
                response_object = {
                    'status': 'failure',
                    'description': 'Forbidden: user is not the sender of this message'
                }
            elif status_code == 404:
                response_object = {
                    'status': 'failure',
                    'description': 'Message not found'
                }
            elif status_code == 500:
                response_object = {
                    'status': 'failure',
                    'description':
                    'Server error: Error in retrieving sender/blacklist',
                }

            return jsonify(response_object), status_code

    response_object = {
        'status': 'success',
        'description': 'Bottlebox retrieved',
        'messages': messages_json
    }

    return jsonify(response_object), 200


def get_pending_bottlebox():
    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:
            
            return response.json(), response.status_code
        
        # build user object from json
        requester_json = response.json()['user']
        requester = User.build_from_json(requester_json)

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500


    # retrieve messages of the requested label for the specified user
    messages = MessageManager.retrieve_messages_by_label(PENDING_LABEL, requester_id)

    messages_json = []

    for message in messages:
        # get all information we need
        message_json, status_code = MessageLogic.get_pending_or_delivered_message(message, requester)

        # check status code
        if status_code == 200:
            messages_json.append(message_json)
        else:
            if status_code == 403:
                response_object = {
                    'status': 'failure',
                    'description': 'Forbidden: user is not the sender of this message'
                }
            elif status_code == 404:
                response_object = {
                    'status': 'failure',
                    'description': 'Message not found'
                }
            elif status_code == 500:
                response_object = {
                    'status': 'failure',
                    'description':
                    'Server error: Error in retrieving sender/blacklist',
                }

            return jsonify(response_object), status_code

    response_object = {
        'status': 'success',
        'description': 'Bottlebox retrieved',
        'messages': messages_json
    }

    return jsonify(response_object), 200


def get_delivered_bottlebox():
    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:
            
            return response.json(), response.status_code
        
        # build user object from json
        requester_json = response.json()['user']
        requester = User.build_from_json(requester_json)

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500


    # retrieve messages of the requested label for the specified user
    messages = MessageManager.retrieve_messages_by_label(DELIVERED_LABEL, requester_id)

    messages_json = []

    for message in messages:
        # get all information we need
        message_json, status_code = MessageLogic.get_pending_or_delivered_message(message, requester)

        # check status code
        if status_code == 200:
            messages_json.append(message_json)
        else:
            if status_code == 403:
                response_object = {
                    'status':
                    'failure',
                    'description':
                    'Forbidden: user is not the sender of this message'
                }
            elif status_code == 404:
                response_object = {
                    'status': 'failure',
                    'description': 'Message not found'
                }
            elif status_code == 500:
                response_object = {
                    'status':
                    'failure',
                    'description':
                    'Server error: Error in retrieving sender/blacklist',
                }

            return jsonify(response_object), status_code

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

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:
            
            return response.json(), response.status_code
        
        # build user object from json
        requester_json = response.json()['user']
        requester = User.build_from_json(requester_json)

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500


    # retrieve the message, if exists
    message = MessageManager.retrieve_message_by_id(RECEIVED_LABEL, message_id)

    message_json, status_code = MessageLogic.get_received_message(message, requester)

    if status_code == 403:
        response_object = {
            'status': 'failure',
            'description': 'Forbidden: user is not a recipient of this message'
        }
    elif status_code == 404:
        response_object = {
            'status': 'failure',
            'description': 'Message not found'
        }
    elif status_code == 500:
        response_object = {
            'status': 'failure',
            'description': 'Server error: Error in retrieving sender/blacklist',
        }
    elif status_code == 200:
        response_object = {
            'status': 'success',
            'description': 'Message retrieved',
            'message': message_json
        }

    return jsonify(response_object), status_code


def get_draft_message(message_id):

    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:
            
            return response.json(), response.status_code
        
        # build user object from json
        requester_json = response.json()['user']
        requester = User.build_from_json(requester_json)

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500


    # retrieving the message, if exists
    message = MessageManager.retrieve_message_by_id(DRAFT_LABEL, message_id)

    message_json, status_code = MessageLogic.get_draft_message(message, requester)

    if status_code == 403:
        response_object = {
            'status': 'failure',
            'description': 'Forbidden: user is not the sender of this message'
        }
    elif status_code == 404:
        response_object = {
            'status': 'failure',
            'description': 'Message not found'
        }
    elif status_code == 500:
        response_object = {
            'status': 'failure',
            'description':
            'Server error: Error in retrieving sender/blacklist',
        }
    elif status_code == 200:
        response_object = {
            'status': 'success',
            'description': 'Message retrieved',
            'message': message_json
        }

    return jsonify(response_object), status_code


def get_pending_message(message_id):

    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:
            
            return response.json(), response.status_code
        
        # build user object from json
        requester_json = response.json()['user']
        requester = User.build_from_json(requester_json)

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500


    # retrieving the message, if exists
    message = MessageManager.retrieve_message_by_id(PENDING_LABEL, message_id)

    # since pending and delivered messages are similar, they share most of the code
    message_json, status_code = MessageLogic.get_pending_or_delivered_message(message, requester)

    if status_code == 403:
        response_object = {
            'status': 'failure',
            'description': 'Forbidden: user is not the sender of this message'
        }
    elif status_code == 404:
        response_object = {
            'status': 'failure',
            'description': 'Message not found'
        }
    elif status_code == 500:
        response_object = {
            'status': 'failure',
            'description':
            'Server error: Error in retrieving sender/blacklist',
        }
    elif status_code == 200:
        response_object = {
            'status': 'success',
            'description': 'Message retrieved',
            'message': message_json
        }

    return jsonify(response_object), status_code


def get_delivered_message(message_id):

    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:
            
            return response.json(), response.status_code
        
        # build user object from json
        requester_json = response.json()['user']
        requester = User.build_from_json(requester_json)

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500


    # retrieving the message, if exists
    message = MessageManager.retrieve_message_by_id(DELIVERED_LABEL, message_id)

    # since pending and delivered messages are similar, they share most of the code
    message_json, status_code = MessageLogic.get_pending_or_delivered_message(message, requester)

    if status_code == 403:
        response_object = {
            'status': 'failure',
            'description': 'Forbidden: user is not the sender of this message'
        }
    elif status_code == 404:
        response_object = {
            'status': 'failure',
            'description': 'Message not found'
        }
    elif status_code == 500:
        response_object = {
            'status': 'failure',
            'description':
            'Server error: Error in retrieving sender/blacklist',
        }
    elif status_code == 200:
        response_object = {
            'status': 'success',
            'description': 'Message retrieved',
            'message': message_json
        }

    return jsonify(response_object), status_code


# UPDATE OPERATIONS


def hide_message(message_id):

    # get info about the requester and the message
    data = request.get_json()
    requester_id = data.get('requester_id')

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:

            return response.json(), response.status_code

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500


    # user must be a recipient of a RECEIVED message
    message = MessageManager.retrieve_message_by_id(RECEIVED_LABEL, message_id)
    message_recipient = MessageManager.retrieve_message_recipient(message_id, requester_id)

    if message is None or message_recipient is None:
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


def report_message(message_id):

    # get info about the requester and the message
    data = request.get_json()
    requester_id = data.get('requester_id')

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:

            return response.json(), response.status_code

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500


    # user must be a recipient of a RECEIVED message
    message = MessageManager.retrieve_message_by_id(RECEIVED_LABEL, message_id)
    message_recipient = MessageManager.retrieve_message_recipient(
        message_id, requester_id)

    if message is None or message_recipient is None:
        response_object = {
            'status': 'failure',
            'description': 'Forbidden: user is not a recipient of this message'
        }
        return jsonify(response_object), 403

    is_reported = ReportManager.is_message_reported(message_id, requester_id)

    if is_reported:
        response_object = {
            'status': 'failure',
            'description': 'Forbidden: already reported'
        }
        return jsonify(response_object), 403

    report = Report()
    report.reporting_user_id = requester_id
    report.message_id = message_id
    report.reporting_user_id = datetime.datetime.now()

    ReportManager.create_report(report)

    response_object = {
        'status': 'success',
        'description': 'Message successfully reported'
    }
    return jsonify(response_object), 200


def modify_draft_message(message_id):

    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')
    content = data.get('content')
    deliver_time = data.get('deliver_time')
    recipients = data.get('recipients')
    new_image = data.get('new_image')
    # TODO SUPPORT IT
    delete_image = data.get('delete_image')
    is_sent = data.get('is_sent')

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:

            return response.json(), response.status_code

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500

    draft_message = MessageManager.retrieve_message_by_id(DRAFT_LABEL, message_id)


    # TODO TODO TODO GUARDA NEW MESSAGE COME E' STRUTTURATO

    # TODO SUPPORT IMAGE DELETION
    '''
    An user can decide to delete current attachment OR to replace it with another one
    They are mutual exclusive but, in case of wrong configuration made
    by the Gateway (delete=True and image provided), image deletion has the precedence
    Note that if delete_image=False and new_image = '' -> keep current attachment
    '''
    # check if the user_id is the sender of the draft message
    if draft_message.sender_id != requester_id:
        response_object = {
            'status': 'failure',
            'description': 'Forbidden: user is not the sender of this message'
        }
        return jsonify(response_object), 403
        
    if delete_image:
        # TODO REMOVE ATTACHMENT
        # TODO REMOVE FOLDER STATIC/ATTACHMENTS/<MESSAGE_ID>
        pass
    elif new_image != '':
        pass
        # TODO replace old attachment with the new one

    # updating message fields
    draft_message.content = content
    draft_message.deliver_time = datetime.datetime.fromisoformat(deliver_time)

    message_new_recipient_ids = []

    # retrieving ids of selected recipients and checking their existance
    for recipient in recipients:
        data = {'requester_id':requester_id}
        try: 
            recipient_user =  requests.get("%s/users/%s" % (USERS_ENDPOINT, str(recipient)),
                                    timeout=REQUESTS_TIMEOUT_SECONDS,
                                    json=data)

            if recipient_user.status_code != 200:

                return recipient_user.json(), recipient_user.status_code
            
            message_new_recipient_ids.append(recipient_user.json()['user']['id'])

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            response_object = {
                'status': 'failure',
                'description': 'Error in retrieving user',
            }
            return jsonify(response_object), 500

    message_current_recipient_ids = MessageManager.retrieve_message_recipients(draft_message.id)
    for recipient_id in message_current_recipient_ids:
        if recipient_id not in message_new_recipient_ids:
            MessageManager.remove_message_recipient(draft_message.id,recipient_id)

    for recipient_user_id in message_new_recipient_ids:
        data = {'requester_id':requester_id}

        try: 
            blacklist = requests.get("%s/blacklist/" % (BLACKLIST_ENDPOINT),
                                    timeout=REQUESTS_TIMEOUT_SECONDS,
                                    json=data)
            
            if blacklist.status_code != 200:
                return blacklist.json(), blacklist.status_code

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            response_object = {
                'status': 'failure',
                'description': 'Error in retrieving user',
            }
            return jsonify(response_object), 500
        
        message_recipient = None
        message_recipient = MessageManager.retrieve_message_recipient(draft_message.id,recipient_user_id)
        blacklist_data = blacklist.json()

        if recipient_user_id in blacklist_data['blacklist']:
            if message_recipient is not None:
                MessageManager.remove_message_recipient(draft_message.id,recipient_user_id)
                message_new_recipient_ids.remove(recipient_user_id)
        else:
            if message_recipient is None:
                msg_recipient = Message_Recipient()
                msg_recipient.id = draft_message.id
                msg_recipient.recipient_id = recipient_user_id
                MessageManager.create_message_recipient(msg_recipient)
        
    # set the message as sent
    # The message is in 'pending' status by now
    if is_sent:
        draft_message.is_sent = True
        
    MessageManager.update_message(draft_message)

    response_object={
        'status': 'success',
        'message': 'Draft modified'
    }
    return response_object,200


# DELETE OPERATIONS


def delete_draft_message(message_id):

    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:
            return response.json(), response.status_code

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500


    # retrieving the message, if exists
    message = MessageManager.retrieve_message_by_id(DRAFT_LABEL, message_id)

    return MessageLogic.delete_message(message, requester_id)


def delete_pending_message(message_id):

    # get info about the requester
    data = request.get_json()
    requester_id = data.get('requester_id')

    user = None

    # check if the requester_id exists
    try:
        data = {'requester_id': requester_id}
        response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:

            return response.json(), response.status_code

        user = response.json()['user']

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500

    message = None
    # retrieving the message, if exists
    message = MessageManager.retrieve_message_by_id(PENDING_LABEL, message_id)

    if message is None:
        response_object = {
            'status':'failure',
            'description':'Pending message not found the sender'
        }
        return response_object, 404 

    if user['id'] != message.sender_id:
        response_object= {
            'status':'failure',
            'description':'Not the sender'
        }
        return response_object, 403    
    
    try: 
        data = {'requester_id': requester_id}
        response = requests.put("%s/users/spend" % (USERS_ENDPOINT),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)

        if response.status_code != 200:

            return response.json(), response.status_code

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        response_object = {
            'status': 'failure',
            'description': 'Error in retrieving user',
        }
        return jsonify(response_object), 500

    return MessageLogic.delete_message(message,requester_id)
    