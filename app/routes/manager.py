from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import mongo   # ✅ This gives access to mongo.db
from bson import ObjectId
from pytz import timezone


manager_bp = Blueprint('manager', __name__)

@manager_bp.route("/team", methods=["GET"])
@jwt_required()
def team_list():
    email = get_jwt_identity()
    users = mongo.db.users

    team = list(users.find({"reporting_to": email}, {
        "_id": 0, "name": 1, "email": 1, "position": 1, "department": 1
    }))

    return jsonify(team), 200

@manager_bp.route("/checkins/pending", methods=["GET"])
@jwt_required()
def manager_pending_checkins():
    email = get_jwt_identity()
    users_col = mongo.db.users
    checkins_col = mongo.db.pending_checkins

    # Step 1: Get all users who report to this manager
    team = users_col.find({"reporting_to": {"$in": [email]}}, {"email": 1})
    team_emails = [u["email"] for u in team]

    # Step 2: Get pending check-ins for those emails
    pending = list(checkins_col.find({"email": {"$in": team_emails}, "status": "Pending"}))
    india = timezone("Asia/Kolkata")

    result = []
    for p in pending:
        ist_time = p["requested_at"].astimezone(india) if p.get("requested_at") else None

        result.append({
            "_id": str(p["_id"]),
            "email": p["email"],
            "date": p["date"],
            "status": p["status"],
            "checkin_time": ist_time.strftime("%I:%M %p") if ist_time else "—"
        })

    return jsonify(result), 200
    
@manager_bp.route("/checkins/approve/<checkin_id>", methods=["POST"])
@jwt_required()
def manager_approve_checkin(checkin_id):
    email = get_jwt_identity()
    users_col = mongo.db.users
    logs_col = mongo.db.logs
    checkins_col = mongo.db.pending_checkins

    checkin = checkins_col.find_one({"_id": ObjectId(checkin_id)})
    if not checkin:
        return jsonify({"msg": "Check-in not found"}), 404

    # ✅ check if manager has rights to approve
    emp = users_col.find_one({"email": checkin["email"]})
    if not emp or email not in emp.get("reporting_to", []):
        return jsonify({"msg": "Unauthorized"}), 403

    # Prevent duplicates
    existing = logs_col.find_one({"email": checkin["email"], "date": checkin["date"]})
    if existing:
        return jsonify({"msg": "Check-in already exists for this date"}), 400

    logs_col.insert_one({
        "email": checkin["email"],
        "date": checkin["date"],
        "checkin": checkin["requested_at"],
        "checkout": None,
        "approved": True
    })

    checkins_col.update_one({"_id": ObjectId(checkin_id)}, {"$set": {"status": "Approved"}})
    return jsonify({"msg": "Check-in approved"}), 200

  
@manager_bp.route("/team-summary", methods=["GET"])
@jwt_required()
def team_attendance_summary():
    email = get_jwt_identity()
    users = mongo.db.users
    logs = mongo.db.logs

    team = list(users.find({"reporting_to": email}, {"email": 1, "name": 1}))
    summaries = []

    for emp in team:
        emp_logs = list(logs.find({"email": emp["email"]}))
        status_count = {
            "Present": 0, "Absent": 0, "Half Day": 0, "Leave": 0, "Holiday": 0
        }
        for log in emp_logs:
            status = log.get("status")
            if status in status_count:
                status_count[status] += 1

        summaries.append({
            "name": emp["name"],
            "email": emp["email"],
            "summary": status_count
        })

    return jsonify(summaries), 200

@manager_bp.route("/checkins/reject/<checkin_id>", methods=["POST"])
@jwt_required()
def manager_reject_checkin(checkin_id):
    email = get_jwt_identity()
    users_col = mongo.db.users
    checkins_col = mongo.db.pending_checkins

    checkin = checkins_col.find_one({"_id": ObjectId(checkin_id)})
    if not checkin:
        return jsonify({"msg": "Check-in not found"}), 404

    emp = users_col.find_one({"email": checkin["email"]})
    if not emp or email not in emp.get("reporting_to", []):
        return jsonify({"msg": "Unauthorized"}), 403

    checkins_col.update_one({"_id": ObjectId(checkin_id)}, {"$set": {"status": "Rejected"}})
    return jsonify({"msg": "Check-in rejected"}), 200

