from flask_mail import Message
from flask import current_app
from app.extensions import mail

def send_email(subject, recipients, body):
    try:
        msg = Message(
            subject=subject,
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
            recipients=recipients,
            body=body
        )
        mail.send(msg)
    except Exception as e:
        print("❌ Failed to send email:", str(e))
      
