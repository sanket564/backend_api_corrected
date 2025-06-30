from flask import Blueprint, current_app
from flask_mail import Message
from app.extensions import mail

test_mail_bp = Blueprint('test_mail', __name__)

@test_mail_bp.route('/send_test_email')
def send_test_email():
    try:
        msg = Message(
            subject="✅ Test Email from Attendance System",
            sender="sanket.b1@outlook.com",  # ✅ Must match MAIL_USERNAME
            recipients=["biradarsanket83@gmail.com"],
            body="This is a test email sent using Outlook SMTP via Flask-Mail."
        )

        # ✅ Safe debug logging
        print("Sending email using:")
        print("MAIL_SERVER:", current_app.config.get("MAIL_SERVER"))
        print("MAIL_PORT:", current_app.config.get("MAIL_PORT"))
        print("MAIL_USERNAME:", current_app.config.get("MAIL_USERNAME"))

        mail.send(msg)
        return "✅ Test email sent successfully!"
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"
