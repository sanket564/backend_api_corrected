from flask import Blueprint
from flask_mail import Message
from app.extensions import mail

test_mail_bp = Blueprint('test_mail', __name__)

@test_mail_bp.route('/send_test_email')
def send_test_email():
    try:
        msg = Message(
            subject="✅ Test Email from Attendance System",
            recipients=["recipient@example.com"],  # 👈 change this to your email
            body="This is a test email sent using Outlook SMTP via Flask-Mail."
        )
        mail.send(msg)
        return "✅ Test email sent successfully!"
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"
