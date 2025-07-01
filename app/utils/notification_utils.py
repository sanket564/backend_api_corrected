from datetime import datetime
from app.extensions import mongo

def create_notification(email, message, type="info"):
    notification = {
        "email": email,
        "message": message,
        "type": type,
        "seen": False,
        "created_at": datetime.utcnow()
    }
    mongo.db.notifications.insert_one(notification)
  
