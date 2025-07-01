from flask_mail import Message
from flask import current_app
from app.extensions import mail, mongo
from datetime import datetime

def send_notification_email(email, subject, body, notif_type="info"):
    try:
        # ✅ Construct email
        msg = Message(
            subject=subject,
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
            recipients=[email],
            body=body
        )

        # ✅ Send it via Flask-Mail
        mail.send(msg)
        print(f"📤 Email sent to: {email} | Subject: {subject}")

        # ✅ Also log it as an in-app notification
        mongo.db.notifications.insert_one({
            "email": email,
            "subject": subject,
            "body": body,
            "type": notif_type,
            "timestamp": datetime.utcnow(),
            "seen": False
        })

    except Exception as e:
        print(f"❌ Email notification failed for {email}: {str(e)}")
