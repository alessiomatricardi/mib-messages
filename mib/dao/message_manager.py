from mib.dao.manager import Manager
from mib.models import Message, Message_Recipient

from typing import List, Union

MESSAGE_STATES = ["pending", "delivered", "received", "drafts"]

class MessageManager(Manager):

    @staticmethod
    def retrieve_messages_by_label(label_, user_id) -> Union[List, None]:
        Manager.check_none(label=label_)
        Manager.check_none(user_id=user_id)

        if label_ not in MESSAGE_STATES:
            return None

        if label_ == "pending": #pending
            messages = Message.query.filter(
                Message.sender_id == user_id, 
                Message.is_sent == True, 
                Message.is_delivered == False
            ).all()
            
            # TODO aggiungere Spacy/profanity filter come dipendenza
            # if the content filter is active, all the messages will be displayed censored
            # if filter.filter_enabled(user.id):
            if False:
                for message in msg:
                   censored_content = filter.check_message_content(message.content)
                   message.content = censored_content 
            return messages
        
        elif label_ == "received": #received
            messages = Message.query.join(Message_Recipient, Message.id == Message_Recipient.id)\
                .add_columns(Message_Recipient.is_read)\
                .filter(
                    Message_Recipient.recipient_id == user_id,
                    Message.is_sent == True,
                    Message.is_delivered == True,
                    Message_Recipient.is_hide == False
                ).all()

            # TODO aggiungere Spacy/profanity filter come dipendenza
            # if the content filter is active, all the messages will be displayed censored
            # if filter.filter_enabled(user.id):
            if False:
                for message in to_return:
                    censored_content = filter.check_message_content(message.content)
                    message.content = censored_content
            
            '''
            messages has the structure below:
            for message in messages
                message[0] -> Message object
                message[1] -> is_read boolean
            
            it has to be handled by the caller
            '''

            return messages
        
        elif label_ == "delivered": #delivered
            messages = Message.query.filter(
                Message.sender_id == user_id,
                Message.is_sent == True,
                Message.is_delivered == True
            ).all()
            
            # TODO aggiungere Spacy/profanity filter come dipendenza
            # if the content filter is active, all the messages will be displayed censored
            # if filter.filter_enabled(user.id):
            if False:
                for message in msg:
                   censored_content = filter.check_message_content(message.content)
                   message.content = censored_content

            return messages

        elif label_ == "drafts": #drafts
            messages = Message.query.filter(
                Message.sender_id == user_id,
                Message.is_sent == False
            ).all()

            # TODO aggiungere Spacy/profanity filter come dipendenza
            # if the content filter is active, all the messages will be displayed censored
            # if filter.filter_enabled(user.id):
            if False:
                for message in msg:
                   censored_content = filter.check_message_content(message.content)
                   message.content = censored_content

            return messages


    def retrieve_message_recipients(message_id) -> List[int]:
        Manager.check_none(message_id=message_id)

        recipients = Message_Recipient.query.filter(Message_Recipient.id == message_id).all()

        return [recipient.recipient_id for recipient in recipients]