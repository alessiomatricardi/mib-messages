import smtplib, ssl
from unittest import result

port = 587  # For starttls
smtp_server = "smtp.gmail.com"

# email and password of a Gmail account used to send emails
sender_email = "squad04ase@gmail.com"
password = "Squad-04-ASE"

# function used to send emails
def send_email(recipient, msg):
    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtp_server,port)
        server.starttls() # Secure the connection
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient, msg)
        result = True
    except Exception:
        result = False
    finally:
        server.quit() 
        return result