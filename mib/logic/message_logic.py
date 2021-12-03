from mib.models import Message
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


class MessageLogic:

    @staticmethod
    def get_received_message(message : Message, requester_id : int):

        # check if the message exists
        if not message:
            return None, 404

        message_id = message.id

        # check if the user_id is a recipient of the message
        message_recipient = MessageManager.retrieve_message_recipient(message_id, requester_id)
        if not message_recipient:
            return None, 403

        # check if the message has not been hidden by user_id
        if message_recipient.is_hide:
            return None, 404

        # get sender informations
        sender = None

        try:
            data = {'requester_id': message.sender_id}
            response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(message.sender_id)),
                                    timeout=REQUESTS_TIMEOUT_SECONDS,
                                    json=data)

            if response.status_code != 200:
                return None, 500

            sender = response.json()['user']

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return None, 500


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

        return message_json, 200


    @staticmethod
    def get_draft_message(message : Message, requester_id : int):
        if not message:
            return None, 404

        message_id = message.id

        # check if the user_id is the sender of the message
        if message.sender_id != requester_id:
            return None, 403

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

        return message_json, 200


    @staticmethod
    def get_pending_or_delivered_message(message : Message, requester_id : int):

        # check if the message exists
        if not message:
            return None, 404

        # check if the user_id is the sender of the message
        if message.sender_id != requester_id:
            return None, 403

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
                return None, 500

            sender = response.json()['user']

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):

            return None, 500

        recipients = MessageManager.retrieve_message_recipients(message.id)

        recipients_list = []
        user = dict()
        user['email'] = 'a.matricardi@studenti.unipi.it'
        user['id'] = 1
        user['firstname'] = 'Alessio'
        user['lastname'] = 'Matricardi'
        user['is_in_blacklist'] = False

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

        return message_json, 200


    @staticmethod
    def delete_message(message : Message, requester_id : int):

        # check if the message exists
        if not message:
            response_object = {
                'status': 'failure',
                'description': 'Message not found'
            }
            return jsonify(response_object), 404

        message_id = message.id

        # check if the user_id is the sender of the message
        if message.sender_id != requester_id:
            response_object = {
                'status': 'failure',
                'description': 'Forbidden: user is not the sender of this message'
            }
            return jsonify(response_object), 403

        recipients = MessageManager.retrieve_message_recipients(message_id)

        for recipient_id in recipients:
            MessageManager.remove_message_recipient(message_id, recipient_id)

        MessageManager.remove_message(message)

        response_object = {
            'status': 'success',
            'description': 'Message successfully deleted'
        }
        return jsonify(response_object), 200