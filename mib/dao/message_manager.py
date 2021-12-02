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
            
            return messages

        elif label_ == "drafts": #drafts
            messages = Message.query.filter(
                Message.sender_id == user_id,
                Message.is_sent == False
            ).all()

            return messages

    @staticmethod
    def retrieve_message_recipients(message_id) -> List[int]:
        Manager.check_none(message_id=message_id)

        recipients = Message_Recipient.query.filter(Message_Recipient.id == message_id).all()

        return [recipient.recipient_id for recipient in recipients]
    
    @staticmethod
    def retrieve_message_by_id(label, message_id) -> Message:

        Manager.check_none(label=label)
        Manager.check_none(message_id=message_id)

        message = None

        if label in ['received', 'delivered']:
            message = Message.query.filter(
                Message.id == message_id, 
                Message.is_sent == True, 
                Message.is_delivered == True
            ).first()
        elif label == 'pending':
            message = Message.query.filter(
                Message.id == message_id,
                Message.is_sent == True, 
                Message.is_delivered == False
            ).first()
        elif label == 'drafts':
            message = Message.query.filter(
                Message.id == message_id, 
                Message.is_sent == False, 
                Message.is_delivered == False
            ).first()
        
        return message
    
    @staticmethod
    def retrieve_message_recipient(message_id, user_id) -> Message_Recipient:
        
        Manager.check_none(message_id=message_id)
        Manager.check_none(user_id=user_id)

        recipient = Message_Recipient.query.filter(
            Message_Recipient.id == message_id,
            Message_Recipient.recipient_id == user_id
        ).first()

        return recipient
    
    @staticmethod
    def set_message_as_read(message_recipient):
        
        Manager.check_none(message_recipient=message_recipient)

        # message has been read by recipient 
        message_recipient.is_read = True
        Manager.update(message_recipient=message_recipient)
    
    @staticmethod
    def remove_message_recipient(message_id, user_id):

        Manager.check_none(message_id=message_id)
        Manager.check_none(user_id=user_id)

        message_recipient = MessageManager.retrieve_message_recipient(message_id, user_id)
        
        Manager.delete(message_recipient)

    @staticmethod
    def hide_message(message_recipient):

        Manager.check_none(message_recipient=message_recipient)

        message_recipient.is_hide = True     
        Manager.update(message_recipient=message_recipient)
