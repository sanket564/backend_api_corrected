from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.extensions import mongo

leave_bp = Blueprint("leave", __name__)


@leave_bp.route("/request", methods=["POST"])
@jwt_required()
def request_leave():
    email = get_jwt_identity()
    leave_requests = mongo.db.leave_requests
    data = request.get_json()
    date = data.get("date")
    reason = data.get("reason")

    if not date or not reason:
        return jsonify({"msg": "Date and reason are required"}), 400

    existing = leave_requests.find_one({"email": email, "date": date})
    if existing:
        return jsonify({"msg": "Leave request already submitted for this date"}), 409

    leave_requests.insert_one({
        "email": email,
        "reason": reason,
        "date": date,
        "status": "Pending",
        "submitted_at": datetime.now()
    })

    return jsonify({"msg": "Leave request submitted"}), 201

@leave_bp.route("/my-requests", methods=["GET"])
@jwt_required()
def my_leave_requests():
    email = get_jwt_identity()
    leave_requests = mongo.db.leave_requests
    reqs = list(leave_requests.find({"email": email}))
    for r in reqs:
        r["_id"] = str(r["_id"])
    return jsonify(reqs), 200
