from mib.dao.manager import Manager
from mib.models import Message, Message_Recipient

from typing import List

class MessageManager(Manager):

    # CREATE OPERATIONS

    @staticmethod
    def create_message(message : Message):
        Manager.create(message=message)

    @staticmethod
    def create_message_recipient(message_recipient: Message_Recipient):
        Manager.create(message_recipient)

    # READ OPERATIONS

    @staticmethod
    def retrieve_messages_by_label(label, user_id) -> List:
        Manager.check_none(label=label)
        Manager.check_none(user_id=user_id)

        messages = []

        if label == "pending":
            messages = Message.query.filter(
                Message.sender_id == user_id,
                Message.is_sent == True,
                Message.is_delivered == False
            ).all()

        elif label == "received":
            messages = Message.query.join(Message_Recipient, Message.id == Message_Recipient.id)\
                .filter(
                    Message_Recipient.recipient_id == user_id,
                    Message.is_sent == True,
                    Message.is_delivered == True,
                    Message_Recipient.is_hide == False
                ).all()

        elif label == "delivered":
            messages = Message.query.filter(
                Message.sender_id == user_id,
                Message.is_sent == True,
                Message.is_delivered == True
            ).all()

        elif label == "drafts":
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
    def retrieve_message_recipient(message_id, recipient_id) -> Message_Recipient:

        Manager.check_none(message_id=message_id)
        Manager.check_none(recipient_id=recipient_id)

        recipient = Message_Recipient.query.filter(
            Message_Recipient.id == message_id,
            Message_Recipient.recipient_id == recipient_id
        ).first()

        return recipient

    # UPDATE OPERATIONS

    @staticmethod
    def update_message(message : Message):
        Manager.update(message)

    @staticmethod
    def set_message_as_read(message_recipient : Message_Recipient):

        Manager.check_none(message_recipient=message_recipient)

        # message has been read by recipient
        message_recipient.is_read = True
        Manager.update(message_recipient=message_recipient)

    @staticmethod
    def hide_message(message_recipient : Message_Recipient):

        Manager.check_none(message_recipient=message_recipient)

        message_recipient.is_hide = True
        Manager.update(message_recipient=message_recipient)

    # DELETE OPERATIONS

    @staticmethod
    def remove_message(message: Message):
        Manager.delete(message)

    @staticmethod
    def remove_message_recipient(message_id, recipient_id):

        Manager.check_none(message_id=message_id)
        Manager.check_none(recipient_id=recipient_id)

        message_recipient = MessageManager.retrieve_message_recipient(message_id, recipient_id)

        Manager.delete(message_recipient)
