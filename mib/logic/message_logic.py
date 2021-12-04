from mib.models import Message
from mib.dao.message_manager import MessageManager
from mib.dao.report_manager import ReportManager
from flask import jsonify
import requests
from mib import app
from mib.emails import send_email
from mib.content_filter import censure_content
from .user import User

USERS_ENDPOINT = app.config['USERS_MS_URL']
BLACKLIST_ENDPOINT = app.config['BLACKLIST_MS_URL']
REQUESTS_TIMEOUT_SECONDS = app.config['REQUESTS_TIMEOUT_SECONDS']


class MessageLogic:

    @staticmethod
    def get_received_message(message : Message, requester : User):

        requester_id = requester.id

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

            sender_json = response.json()['user']
            sender = User.build_from_json(sender_json)

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return None, 500


        # check if the message is already read. If not, set it as read and send a notification to the sender
        if not message_recipient.is_read:

            MessageManager.set_message_as_read(message_recipient)

            # TODO interazione con user per ricavare il nome dell'utente recipient
            email_message = "Subject: Message notification\n\nThe message you sent to %s %s (%s) has been read." \
                % (requester.firstname, requester.lastname, requester.email)


            email = sender.email

            send_email(email, email_message)

        # check if the sender is in our blacklist, in order to don't permit to see his profile
        try:
            data = {'requester_id': message.sender_id}
            response = requests.get("%s/blacklist" %
                                    (BLACKLIST_ENDPOINT),
                                    timeout=REQUESTS_TIMEOUT_SECONDS,
                                    json=data)

            if response.status_code != 200:
                return None, 500

            # status OK, retrieve blacklist
            blacklist = response.json()['blacklist']

            is_sender_in_blacklist = message.sender_id in blacklist

        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout):
            return None, 500

        message_json = message.serialize()

        # store info of the sender
        message_json['sender_firstname'] = sender.firstname
        message_json['sender_lastname'] = sender.lastname
        message_json['sender_email'] = sender.email

        # store that the sender is into blacklist or not
        message_json['is_sender_in_blacklist'] = is_sender_in_blacklist

        # store that the message is read or not
        message_json['is_read'] = message_recipient.is_read

        # censure the message if the user has content filter enabled
        if requester.content_filter_enabled:
            censored_content = censure_content(message.content)
            message_json['content'] = censored_content

        # check if the user already reported this message
        reported = ReportManager.is_message_reported(message_id, requester_id)
        message_json['is_reported'] = reported

        return message_json, 200


    @staticmethod
    def get_draft_message(message: Message, requester: User):

        requester_id = requester.id

        if not message:
            return None, 404

        message_id = message.id

        # check if the user_id is the sender of the message
        if message.sender_id != requester_id:
            return None, 403

        recipients_ids = MessageManager.retrieve_message_recipients(message_id)

        # API gateway will use this field to render the form
        recipient_emails = []

        # checks that already saved recipients are still available (they could have become inactive or blocked/blocking user)
        for recipient_id in recipients_ids:

            recipient_is_in_blacklist = False

            # get recipient information
            try:
                data = {'requester_id': requester_id}
                response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(recipient_id)),
                                        timeout=REQUESTS_TIMEOUT_SECONDS,
                                        json=data)

                # if the response code is 403 the recipient is into our blacklist so we have to remove him
                if response.status_code == 403:
                    recipient_is_in_blacklist = True

                elif response.status_code != 200:
                    return None, 500

                recipient_json = response.json()['user']
                recipient = User.build_from_json(recipient_json)

                if not recipient.is_active or recipient_is_in_blacklist:
                    # remove user from recipients
                    MessageManager.remove_message_recipient(message_id, recipient_id)
                else:
                    # add it to emails to be returned
                    recipient_emails.append(recipient.email)

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                return None, 500


        message_json = message.serialize()

        # store recipients
        message_json['recipients'] = recipient_emails

        return message_json, 200


    @staticmethod
    def get_pending_or_delivered_message(message : Message, requester : User):

        requester_id = requester.id

        # check if the message exists
        if not message:
            return None, 404

        # check if the user_id is the sender of the message
        if message.sender_id != requester_id:
            return None, 403


        recipients_ids = MessageManager.retrieve_message_recipients(message.id)

        recipients_list = []

        # checks if a recipient has blocked (or has been blocked by) the sender (user who calls this method)
        for recipient_id in recipients_ids:

            recipient_is_in_blacklist = False

            # get recipient information
            try:
                data = {'requester_id': requester_id}
                response = requests.get("%s/users/%s" %
                                        (USERS_ENDPOINT, str(recipient_id)),
                                        timeout=REQUESTS_TIMEOUT_SECONDS,
                                        json=data)

                # if the response code is 403 the recipient is into our blacklist so we have to remove him
                if response.status_code == 403:
                    recipient_is_in_blacklist = True

                elif response.status_code != 200:
                    return None, 500

                recipient_json = response.json()['user']
                recipient = User.build_from_json(recipient_json)

                # create a dictionary, fill its fields from recipient info and append into the list

                user = dict()
                user['email'] = recipient.email
                user['id'] = recipient.id
                user['firstname'] = recipient.firstname
                user['lastname'] = recipient.lastname
                user['is_in_blacklist'] = recipient_is_in_blacklist

                recipients_list.append(user)

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout):
                return None, 500


        message_json = message.serialize()

        # store recipients
        message_json['recipients'] = recipients_list

        # censure the message if the user has content filter enabled
        if requester.content_filter_enabled:
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