from mib.dao.message_manager import MessageManager
from mib.dao.report_manager import ReportManager
from flask import jsonify
import requests
from mib import app
from mib.emails import send_email
from mib.content_filter import ContentFilter


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

# GET /<user_id>/messages/<label>/<message_id>
# GET /messages/<label>/<message_id>
# Headers: .... Authrization: token = user
def get_message(user_id, label, message_id):

    # TODO L'API GATEWAY DEVE CONTROLLARE SE ID E` INTERO
    # TODO API GATEWAY
    #if label not in ['received', 'delivered', 'pending', 'drafts']:
        #abort(404)
    #if label != 'draft' and request.method == 'POST':
        #abort(404)

    if label == 'received':
        
        message = MessageManager.retrieve_message_by_id(label, message_id)

        if not message:
            response_object = {
                'status' : 'failure',
                'message' : 'Message not found'
            }
            return jsonify(response_object), 404

        # check if the user_id is into recipients of the message
        message_recipient = MessageManager.retrieve_message_recipient(message_id, user_id)

        if not message_recipient:
            response_object = {
                'status' : 'failure',
                'message' : 'Forbidden: user is not a recipient of this message'
            }
            return jsonify(response_object), 403

        # check if is_read == False. If so, set it to True and send notification to sender
        if not message_recipient.is_read:

            MessageManager.set_message_as_read(message_recipient)
            
            # send email to the send
            sender_id = message.sender_id

            # TODO interazione con user per ricavare il nome dell'utente
            email_message = "Subject: Message notification\n\nThe message you sent to " + "PEPPINO" + " has been read."
            
            # TODO interazione con user per ricavare l'email dell'utente
            #email = db.session.query(User).filter(User.id == message_sender_id).first().email
            email = 'a.matricardi@studenti.unipi.it'

            send_email(email, email_message)
        
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
    
        message_json = message.serialize()

        # censure the message if the user has content filter enabled

        # TODO get info from the user
        # GET /users/<id>/content_filter
        sender = None

        try:
            response = requests.get("%s/users/%s/list/%s" % (USERS_ENDPOINT, str(user_id), str(user_id)),
                                    timeout=REQUESTS_TIMEOUT_SECONDS)
            
            if response.status_code != 200:
                return response.json(), response.status_code
            
            sender = response.json()['user']

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):

            response_object = {
                'status': 'failure',
                'message': 'Error in retrieving user',
            }
            return jsonify(response_object), 500
        
        message_json = message.serialize()

        # censure the message if the user has content filter enabled
        if sender['content_filter_enabled']:
            censored_content = ContentFilter.censure_content(message.content)
            message_json['content'] = censored_content
        
        # check if the user already reported this message
        reported = ReportManager.is_message_reported(message_id, user_id)
        message_json['reported'] = reported

        response_object = {
            'status' : 'success',
            'message' : 'Message retrieved',
            'messaggio_da_restituire' : message_json
        }
        return jsonify(response_object), 200
    
    elif label == 'drafts':

        # retrieving the message, if exists
        message = MessageManager.retrieve_message_by_id(label, message_id)

        if not message:
            response_object = {
                'status' : 'failure',
                'message' : 'Message not found'
            }
            return jsonify(response_object), 404
        
        # check if the user_id is the sender of the message
        if message.sender_id != user_id:
            response_object = {
                'status' : 'failure',
                'message' : 'Forbidden: user is not the sender of this message'
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
                MessageManager.remove_message_recipient(message_id, user_id)
            else:
                recipient_emails.append(user['email'])


        message_json = message.serialize()
        message_json['recipients'] = recipient_emails

        response_object = {
            'status' : 'success',
            'message' : 'Message retrieved',
            'content' : message_json
        }
        return jsonify(response_object), 200

    elif label in ['pending', 'delivered']:

        # retrieving the message, if exists
        message = MessageManager.retrieve_message_by_id(label, message_id)

        if not message:
            response_object = {
                'status' : 'failure',
                'message' : 'Message not found'
            }
            return jsonify(response_object), 404
        
        # check if the user_id is the sender of the message
        if message.sender_id != user_id:
            response_object = {
                'status' : 'failure',
                'message' : 'Forbidden: user is not the sender of this message'
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

        # retrieve sender info from db

        sender = None

        try:
            response = requests.get("%s/users/%s/list/%s" % (USERS_ENDPOINT, str(user_id), str(user_id)),
                                    timeout=REQUESTS_TIMEOUT_SECONDS)
            
            if response.status_code != 200:
                return response.json(), response.status_code
            
            sender = response.json()['user']

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):

            response_object = {
                'status': 'failure',
                'message': 'Error in retrieving user',
            }
            return jsonify(response_object), 500
        
        message_json = message.serialize()

        # censure the message if the user has content filter enabled
        if sender['content_filter_enabled']:
            censored_content = ContentFilter.censure_content(message.content)
            message_json['content'] = censored_content

        response_object = {
            'status' : 'success',
            'message' : 'Message retrieved',
            'content' : message_json
        }
        return jsonify(response_object), 200 

    else:
        response_object = {
            'status' : 'failure',
            'message' : 'Wrong label'
        }
        return jsonify(response_object), 400 