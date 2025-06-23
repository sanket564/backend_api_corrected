from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.extensions import mongo
from bson import ObjectId


leave_bp = Blueprint("leave", __name__)


# @leave_bp.route("/request", methods=["POST"])
# @jwt_required()
# def request_leave():
#     email = get_jwt_identity()
#     leave_requests = mongo.db.leave_requests
#     data = request.get_json()
#     date = data.get("date")
#     reason = data.get("reason")

#     if not date or not reason:
#         return jsonify({"msg": "Date and reason are required"}), 400

#     existing = leave_requests.find_one({"email": email, "date": date})
#     if existing:
#         return jsonify({"msg": "Leave request already submitted for this date"}), 409

#     leave_requests.insert_one({
#         "email": email,
#         "reason": reason,
#         "date": date,
#         "status": "Pending",
#         "submitted_at": datetime.now()
#     })

#     return jsonify({"msg": "Leave request submitted"}), 201

# @leave_bp.route("/request", methods=["POST"])
# @jwt_required()
# def request_leave():
#     email = get_jwt_identity()
#     leave_requests = mongo.db.leave_requests
#     data = request.get_json()

#     from_date = data.get("from_date")
#     to_date = data.get("to_date")
#     reason = data.get("reason")

#     if not from_date or not to_date or not reason:
#         return jsonify({"msg": "From date, to date, and reason are required"}), 400

#     # Check for overlapping leave
#     existing = leave_requests.find_one({
#         "email": email,
#         "$or": [
#             {"from_date": {"$lte": to_date}, "to_date": {"$gte": from_date}}
#         ]
#     })
#     if existing:
#         return jsonify({"msg": "Leave request already exists for this range"}), 409

#     leave_requests.insert_one({
#         "email": email,
#         "reason": reason,
#         "from_date": from_date,
#         "to_date": to_date,
#         "status": "Pending",
#         "submitted_at": datetime.now()
#     })

#     return jsonify({"msg": "Leave request submitted"}), 201
@leave_bp.route("/request", methods=["POST"])
@jwt_required()
def request_leave():
    email = get_jwt_identity()
    users_col = mongo.db.users
    leave_requests = mongo.db.leave_requests
    data = request.get_json()

    from_date = data.get("from_date")
    to_date = data.get("to_date")
    reason = data.get("reason")

    if not from_date or not to_date or not reason:
        return jsonify({"msg": "From date, to date, and reason are required"}), 400

    # Prevent overlap
    existing = leave_requests.find_one({
        "email": email,
        "$or": [
            {"from_date": {"$lte": to_date}, "to_date": {"$gte": from_date}}
        ]
    })
    if existing:
        return jsonify({"msg": "Leave request already exists for this range"}), 409

    # Pull approvers from user profile
    user = users_col.find_one({"email": email})
    approver_chain = user.get("reporting_to", [])
    current_approver = approver_chain[0] if approver_chain else None

    leave_requests.insert_one({
        "email": email,
        "from_date": from_date,
        "to_date": to_date,
        "reason": reason,
        "status": "Pending",
        "approver_chain": approver_chain,
        "current_approver": current_approver,
        "approval_logs": [],
        "submitted_at": datetime.now()
    })

    return jsonify({"msg": "Leave request submitted"}), 201



# @leave_bp.route("/my-requests", methods=["GET"])
# @jwt_required()
# def my_leave_requests():
#     email = get_jwt_identity()
#     leave_requests = mongo.db.leave_requests
#     reqs = list(leave_requests.find({"email": email}))
#     for r in reqs:
#         r["_id"] = str(r["_id"])
#     return jsonify(reqs), 200

@leave_bp.route("/my-requests", methods=["GET"])
@jwt_required()
def my_leave_requests():
    email = get_jwt_identity()
    leave_requests = mongo.db.leave_requests

    reqs = list(leave_requests.find({"email": email}).sort("submitted_at", -1))
    for r in reqs:
        r["_id"] = str(r["_id"])
    return jsonify(reqs), 200

@leave_bp.route("/approve/<leave_id>", methods=["POST"])
@jwt_required()
def approve_leave(leave_id):
    email = get_jwt_identity()
    leave_requests = mongo.db.leave_requests

    req = leave_requests.find_one({"_id": ObjectId(leave_id)})
    if not req:
        return jsonify({"msg": "Leave request not found"}), 404

    if req["status"] != "Pending":
        return jsonify({"msg": "Request is already resolved"}), 400

    if req["current_approver"] != email:
        return jsonify({"msg": "You are not authorized to approve this"}), 403

    data = request.get_json()
    action = data.get("action")  # should be "approve" or "reject"

    if action not in ("approve", "reject"):
        return jsonify({"msg": "Invalid action"}), 400

    approval_log = {
        "by": email,
        "status": "Approved" if action == "approve" else "Rejected",
        "at": datetime.now()
    }

    update = {
        "$push": {"approval_logs": approval_log}
    }

    if action == "reject":
        update["$set"] = {
            "status": "Rejected",
            "current_approver": None,
            "updated_at": datetime.now()
        }
    else:  # approved
        chain = req.get("approver_chain", [])
        idx = chain.index(email)
        if idx + 1 < len(chain):
            update["$set"] = {
                "current_approver": chain[idx + 1],
                "updated_at": datetime.now()
            }
        else:
            update["$set"] = {
                "status": "Accepted",
                "current_approver": None,
                "updated_at": datetime.now()
            }

    leave_requests.update_one({"_id": ObjectId(leave_id)}, update)
    return jsonify({"msg": f"Leave {action}d successfully"}), 200

