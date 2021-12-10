from logging import Manager
from os import name
import os
import re
from celery import Celery
from celery.schedules import crontab

import datetime
from sqlalchemy.orm import aliased

from mib.emails import send_email

import random

import requests


_APP = None

if os.environ.get('DOCKER_IN_USE') is not None:
    BACKEND = BROKER = 'redis://redis_messages:6379'
else:
    BACKEND = BROKER = 'redis://localhost:6379'

celery = Celery(__name__, backend=BACKEND, broker=BROKER) 


celery.conf.timezone = 'Europe/Rome' # set timezone to Rome

#celery.conf.task_route = {"deliver_message_and_send_notification" : {"queue" : "message-queue"},}

# 
# 1st task: definition of a periodic task that checks if the lottery needs to be performed.
# for simplicity, the lottery is performed on the 15th of every month for each users, independently from the registration date
# 
celery.conf.beat_schedule = {
    'deliver_message_and_send_notification': {
        'task': 'deliver_message_and_send_notification',    # name of the task to execute
        'schedule': 20.0 # crontab()                               # frequency of execution (every 1 min)
    },
}
 
@celery.task(name="deliver_message_and_send_notification")
def deliver_message_and_send_notification():
    global _APP
    global USERS_ENDPOINT
    global REQUESTS_TIMEOUT_SECONDS
    # lazy init
    if _APP is None:
        from mib import create_app
        app = create_app()
        USERS_ENDPOINT = app.config['USERS_MS_URL']
        REQUESTS_TIMEOUT_SECONDS = app.config['REQUESTS_TIMEOUT_SECONDS']
        _APP = app
    else:
        app = _APP
    
    with app.app_context():
        from mib.dao.message_manager import MessageManager

        # retrieves the messages that need to be delivered and notified
        messages = MessageManager.retrieve_messages_to_deliver()

        if len(messages) == 0: # no messages requires notification
            return "No notifications have to be sent"
        else: # there is at least 1 message to be notified and updated
            for msg in messages: 
                
                # retrieve the list of recipients id of the message msg
                recipient_list = MessageManager.retrieve_message_recipients(msg.id)

                data = {
                    'requester_id' : msg.sender_id
                }

                requester_id = msg.sender_id
                
                # retrieve the data of the sender making a request to the User microservice
                response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(requester_id)),
                                timeout=REQUESTS_TIMEOUT_SECONDS,
                                json=data)
                
                if response.status_code != 200:
                    return response.json(), response.status_code
                
                sender_json = response.json()['user']
                
                # take only the firstname and lastname, which will be used for the email
                sender_firstname, sender_lastname = sender_json['firstname'], sender_json['lastname']


                for recipient_id in recipient_list:
                
                    data = {
                        'requester_id' : msg.sender_id
                    }
                    
                    # for each recipient, the data are retrieved from the User microservice
                    response = requests.get("%s/users/%s" % (USERS_ENDPOINT, str(recipient_id)),
                                    timeout=REQUESTS_TIMEOUT_SECONDS,
                                    json=data)

                    if response.status_code != 200:
                        return response.json(), response.status_code
                
                    recipient_json = response.json()['user']

                    # the email of the recipient is saved so to send a notification
                    recipient_email = recipient_json['email']

                    # send the notificaiton to the recipient
                    message = f'Subject: You received a new message!\n\n{sender_firstname} {sender_lastname} has sent you a message.'
                    send_email(recipient_email, message)
                
                # update the message only ater all the recipients have been notified
                msg.is_delivered = True
                MessageManager.update_message(msg)

            return "Messages and corresponding notification sent!"