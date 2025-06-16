from app.extensions import mongo
from datetime import datetime

def get_logs_col():
    return mongo.db.logs

def get_pending_checkins_col():
    return mongo.db.pending_checkins

def get_leave_requests_col():
    return mongo.db.leave_requests

def create_pending_checkin(email, date, requested_at):
    return get_pending_checkins_col().insert_one({
        "email": email,
        "date": date,
        "requested_at": requested_at,
        "status": "Pending"
    })

def log_attendance(email, date, checkin_time):
    return get_logs_col().insert_one({
        "email": email,
        "date": date,
        "checkin": checkin_time,
        "checkout": None,
        "approved": True
    })

def update_checkout(log_id, checkout_time):
    return get_logs_col().update_one(
        {"_id": log_id},
        {"$set": {"checkout": checkout_time}}
    )

def submit_leave_request(email, date, reason):
    return get_leave_requests_col().insert_one({
        "email": email,
        "reason": reason,
        "date": date,
        "status": "Pending",
        "submitted_at": datetime.now()
    })
