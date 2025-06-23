from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

manager_bp = Blueprint('manager_bp', __name__)

@manager_bp.route("/team", methods=["GET"])
@jwt_required()
def team_list():
    email = get_jwt_identity()
    users = mongo.db.users

    team = list(users.find({"reporting_to": email}, {
        "_id": 0, "name": 1, "email": 1, "position": 1, "department": 1
    }))

    return jsonify(team), 200
  
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
