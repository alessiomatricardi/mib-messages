from mib.dao.message_manager import MessageManager
from flask import jsonify
import requests
from mib import app
from mib.emails import send_email


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

        # checking if the current_user is into recipients of the message
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
        

    response_object = {
        'status' : 'success',
        'message' : 'Message retrieved',
        'messaggio_da_restituire' : message.serialize()
    }
    return jsonify(response_object), 200 
'''    
    
    # case label is draft
    elif label == 'draft':

        msg_logic = MessageLogic()
        draft_logic = DraftLogic()

        # rendering the draft detail
        if request.method == 'GET':
            form = MessageForm()

            form.recipients.choices = msg_logic.get_list_of_recipients_email(current_user.id)

            # retrieving the message, if exists
            detailed_message = draft_logic.retrieve_draft(id)
            if not detailed_message:
                abort(404)

            detailed_message = detailed_message[0]

            recipients = []
            # recipients_id = []
            recipients_emails = []

            # checking if the current user is the sender, then retrieving recipients of draft
            if detailed_message.sender_id == current_user.id:
                recipients = draft_logic.retrieve_current_draft_recipients(id)
            else:
                abort(404)

            # checking that already saved recipients are still available (they could have become inactive or blocked/blocking user)
            for recipient in recipients:
                blacklist_istance = draft_logic.recipient_blacklist_status(current_user.id,recipient.id)
                if len(blacklist_istance) > 0 or not recipient.is_active:
                    
                    # the user is no longer available to receive messages from current_user either being inactive or being blocked/blocking
                    flash("The user " + str(recipient.email) + " is no longer avaiable")
                    
                    if not draft_logic.remove_unavailable_recipient(detailed_message.id,recipient.id):
                        abort(500)
                else:
                    # the saved recipient is still available
                    recipients_emails.append(recipient.email)

            # defining format of datetime in order to insert it in html form
            deliver_time = detailed_message.deliver_time.strftime("%Y-%m-%dT%H:%M")

            form.content.data = detailed_message.content

            # returning the draft html page
            return render_template("modify_draft.html", form = form, recipients_emails = recipients_emails, deliver_time = deliver_time, attachment = detailed_message.image, message_id = detailed_message.id)

        # else = Drafts POST method: deleting draft or submitting modification/send request
        elif request.method == 'POST':

            form = request.form

            # retrieving the draft to send, modifiy or delete it
            detailed_message = draft_logic.retrieve_draft(id)
            # checks that the draft exists
            if not detailed_message:
                abort(404)

            detailed_message = detailed_message[0]

            recipients = []
            recipients_id = []
            recipients_emails = []

            # checking if the current user is the sender of draft
            if not detailed_message.sender_id == current_user.id:
                abort(404)

            # delete draft from db, eventual image in filesystem and all message_recipients instances
            if form['submit'] == 'Delete draft':

                if not draft_logic.delete_draft(detailed_message):
                    abort(500)

                return render_template("index.html")

            # Now form['submit'] == 'Send bottle' or 'Save Draft'

            # checking if there's new recipients for the draft
            for recipient_email in form.getlist('recipients'):

                # retrieving id of recipient
                recipient_id = msg_logic.email_to_id(recipient_email)

                # add recipient to draft if not already stored
                if not draft_logic.update_recipients(detailed_message,recipient_id):
                    abort(500)

            # update content of message: if the content is not changed, it'll store the same value
            if not draft_logic.update_content(detailed_message,form):
                abort(500)
            # update the deliver time for the draft
            if not draft_logic.update_deliver_time(detailed_message,form):
                abort(500)

            # checking if there is a new attached image in the form
            if request.files and request.files['attach_image'].filename != '':

                # checking if there's a previous attached image, if so we delete it
                if detailed_message.image != '':

                    if not draft_logic.delete_previously_attached_image(detailed_message):
                        abort(500)

                # retrieving newly attached image
                file = request.files['attach_image']

                # proper controls on the given file
                if msg_logic.validate_file(file):

                    if not draft_logic.update_attached_image(detailed_message,file):
                        abort(500)

                else:
                    # control on filename fails
                    flash('Insert an image with extention: .png , .jpg, .jpeg, .gif')
                    return redirect('/messages/draft/' + str(detailed_message.id))

            # the draft is sent and its is_sent attribute is set to 1, from now on it's no longer possible to modify it
            # in order to stop it, it'll be necessary to spend lottery points
            if form['submit'] == 'Send bottle':
                if not draft_logic.send_draft(detailed_message):
                    abort(500)

            return render_template("index.html")


    else: # case label is pending or delivered

        # checks that message exists
        if label == 'pending':
            detailed_message = bottlebox_logic.retrieve_pending_message(id)
        else:
            detailed_message = bottlebox_logic.retrieve_delivered_message(id)

        if not detailed_message:
            abort(404)

        detailed_message = detailed_message[0]

        # checking if the current user is the sender
        if detailed_message.sender_id == current_user.id:
            recipients = bottlebox_logic.retrieve_recipients(id)
        else:
            abort(404)

        other_id = None

        # checks if a recipient has blocked the current_user or has been blocked
        for i in range(len(recipients)):
            other_id = recipients[i].id

            blacklist_istance = bottlebox_logic.user_blacklist_status(other_id,current_user.id)

            # appends to blocked_info a tuple to link the respective recipient and its blacklist status
            if not blacklist_istance:
                blocked_info.append([recipients[i], False])
            else:
                blocked_info.append([recipients[i], True])

    # retrieving sender info from db
    sender = User.query.where(User.id == detailed_message.sender_id)[0]
    sender_name = sender.firstname + ' ' + sender.lastname
    sender_name = bottlebox_logic.retrieve_sender_info(detailed_message)

    reportForm = ReportForm(message_id = id)
    hideForm = HideForm(message_id = id)

    filter = ContentFilterLogic()

    if filter.filter_enabled(current_user.id):
        censored_content = filter.check_message_content(detailed_message.content)
        detailed_message.content = censored_content

    # has the user already reported this message?
    query = db.session.query(Report).filter(Report.message_id == detailed_message.id, Report.reporting_user_id == current_user.id).first()
    reported = query is not None

    return render_template('message_detail.html', hideForm = hideForm, reportForm = reportForm, message = detailed_message, sender_name = sende
    
'''