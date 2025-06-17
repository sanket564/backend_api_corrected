from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from dateutil import parser

from app.extensions import mongo

attendance_bp = Blueprint("attendance", __name__)

# @attendance_bp.route("/checkin", methods=["POST"])
# @jwt_required()
# def checkin():
#     logs_col = mongo.db.logs
#     pending_checkins_col = mongo.db.pending_checkins

#     email = get_jwt_identity()
#     data = request.get_json()
#     dt = datetime.strptime(data["datetime"], "%Y-%m-%dT%H:%M")
#     date_str = dt.strftime('%Y-%m-%d')

#     if logs_col.find_one({"email": email, "date": date_str}):
#         return jsonify({"msg": "Already checked in on this day"}), 400
#     if pending_checkins_col.find_one({"email": email, "date": date_str, "status": "Pending"}):
#         return jsonify({"msg": "Check-in request already submitted"}), 400

#     pending_checkins_col.insert_one({
#         "email": email,
#         "date": date_str,
#         "requested_at": dt,
#         "status": "Pending"
#     })

#     return jsonify({"msg": "Check-in request submitted. Awaiting admin approval."}), 200
@attendance_bp.route("/checkin", methods=["POST"])
@jwt_required()
def checkin():
    logs_col = mongo.db.logs
    pending_checkins_col = mongo.db.pending_checkins
    users_col = mongo.db.users

    email = get_jwt_identity()
    data = request.get_json()

    try:
        dt = datetime.strptime(data["datetime"], "%Y-%m-%dT%H:%M")
    except:
        return jsonify({"msg": "Invalid datetime format"}), 400

    today = datetime.now().date()
    checkin_date = dt.date()

    user = get_user_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    doj = datetime.strptime(user.get("doj"), "%Y-%m-%d").date()

    # Date validations
    if checkin_date != today:
        return jsonify({"msg": "Check-in is only allowed for today"}), 400
    if checkin_date < doj:
        return jsonify({"msg": "Check-in date cannot be before Date of Joining"}), 400
    if checkin_date > today:
        return jsonify({"msg": "Check-in date cannot be in the future"}), 400

    date_str = dt.strftime('%Y-%m-%d')

    if logs_col.find_one({"email": email, "date": date_str}):
        return jsonify({"msg": "Already checked in on this day"}), 400

    if pending_checkins_col.find_one({"email": email, "date": date_str, "status": "Pending"}):
        return jsonify({"msg": "Check-in request already submitted"}), 400

    # Check yesterday's checkout
    yesterday = today - timedelta(days=1)
    yesterday_log = logs_col.find_one({"email": email, "date": str(yesterday)})
    if yesterday_log and "checkin" in yesterday_log and not yesterday_log.get("checkout"):
        return jsonify({"msg": "Yesterday's checkout is pending. Please check out for yesterday before checking in today."}), 400

    pending_checkins_col.insert_one({
        "email": email,
        "date": date_str,
        "requested_at": dt,
        "status": "Pending"
    })

    return jsonify({"msg": "Check-in request submitted. Awaiting admin approval."}), 200

# @attendance_bp.route("/checkout", methods=["POST"])
# @jwt_required()
# def checkout():
#     logs_col = mongo.db.logs

#     email = get_jwt_identity()
#     data = request.get_json()
#     checkout_dt = datetime.strptime(data["datetime"], "%Y-%m-%dT%H:%M")

#     log = logs_col.find_one(
#         {"email": email, "checkin": {"$exists": True}, "checkout": None},
#         sort=[("date", -1)]
#     )
#     if not log:
#         return jsonify({"msg": "Please check-in first"}), 400

#     checkin_dt = parser.parse(f"{log['date']} {log['checkin']}") \
#         if isinstance(log["checkin"], str) else log["checkin"]

#     if checkout_dt <= checkin_dt:
#         return jsonify({"msg": "Check-out must be after check-in"}), 400

#     logs_col.update_one({"_id": log["_id"]}, {"$set": {"checkout": checkout_dt}})
#     return jsonify({"msg": "Checked out successfully"}), 200

@attendance_bp.route("/checkout", methods=["POST"])
@jwt_required()
def checkout():
    logs_col = mongo.db.logs
    users_col = mongo.db.users

    email = get_jwt_identity()
    data = request.get_json()

    try:
        checkout_dt = datetime.strptime(data["datetime"], "%Y-%m-%dT%H:%M")
    except:
        return jsonify({"msg": "Invalid datetime format"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    doj = datetime.strptime(user.get("doj"), "%Y-%m-%d").date()
    checkout_date = checkout_dt.date()
    today = datetime.now().date()

    if checkout_date != today:
        return jsonify({"msg": "Checkout is only allowed for today"}), 400
    if checkout_date < doj:
        return jsonify({"msg": "Checkout date cannot be before Date of Joining"}), 400
    if checkout_date > today:
        return jsonify({"msg": "Checkout date cannot be in the future"}), 400

    log = logs_col.find_one({
        "email": email,
        "date": checkout_dt.strftime('%Y-%m-%d'),
        "checkin": {"$exists": True},
        "approved": True,
        "checkout": None
    })

    if not log:
        return jsonify({"msg": "You can only check out after approved check-in and not previously checked out"}), 400

    checkin_dt = parser.parse(f"{log['date']} {log['checkin']}") \
        if isinstance(log["checkin"], str) else log["checkin"]

    if checkout_dt <= checkin_dt:
        return jsonify({"msg": "Check-out must be after check-in"}), 400

    logs_col.update_one({"_id": log["_id"]}, {"$set": {"checkout": checkout_dt}})
    return jsonify({"msg": "Checked out successfully"}), 200


@attendance_bp.route("/history", methods=["GET"])
@jwt_required()
def attendance_history():
    logs_col = mongo.db.logs

    email = get_jwt_identity()
    logs = list(logs_col.find({"email": email}).sort("date", -1))
    for log in logs:
        log["_id"] = str(log["_id"])
        for k in ("checkin", "checkout"):
            if isinstance(log.get(k), datetime):
                log[k] = log[k].strftime("%Y-%m-%dT%H:%M:%S")
    return jsonify(logs), 200
