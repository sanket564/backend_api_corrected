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
    from bson import ObjectId
    email = get_jwt_identity()
    leave_requests = mongo.db.leave_requests
    users_col = mongo.db.users
    holidays_col = mongo.db.holidays

    req = leave_requests.find_one({"_id": ObjectId(leave_id)})
    if not req:
        return jsonify({"msg": "Leave request not found"}), 404

    if req["status"] != "Pending":
        return jsonify({"msg": "Request is already resolved"}), 400

    if req["current_approver"] != email:
        return jsonify({"msg": "You are not authorized to approve this"}), 403

    data = request.get_json()
    action = data.get("action")
    if action not in ("approve", "reject"):
        return jsonify({"msg": "Invalid action"}), 400

    approval_log = {
        "by": email,
        "status": "Approved" if action == "approve" else "Rejected",
        "at": datetime.now()
    }

    update = {"$push": {"approval_logs": approval_log}}

    if action == "reject":
        update["$set"] = {
            "status": "Rejected",
            "current_approver": None,
            "updated_at": datetime.now()
        }
    else:
        chain = req.get("approver_chain", [])
        idx = chain.index(email)

        today_str = datetime.now().strftime("%Y-%m-%d")

        # Find the next available approver
        next_approver = None
        for next_email in chain[idx + 1:]:
            # Check if next approver is on leave
            leave_conflict = mongo.db.leave_requests.find_one({
                "email": next_email,
                "status": "Accepted",
                "from_date": {"$lte": today_str},
                "to_date": {"$gte": today_str}
            })

            # Check if today is a holiday (and skip approver if it is)
            is_holiday = holidays_col.find_one({"date": today_str})

            if not leave_conflict and not is_holiday:
                next_approver = next_email
                break

        if next_approver:
            update["$set"] = {
                "current_approver": next_approver,
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

@leave_bp.route("/pending-approvals", methods=["GET"])
@jwt_required()
def pending_approvals():
    email = get_jwt_identity()
    leave_requests = mongo.db.leave_requests

    pending = list(leave_requests.find({
        "status": "Pending",
        "current_approver": email
    }).sort("submitted_at", -1))

    for req in pending:
        req["_id"] = str(req["_id"])
    return jsonify(pending), 200

# @leave_bp.route("/my-leave-balance", methods=["GET"])
# @jwt_required()
# def get_leave_balance():
#     email = get_jwt_identity()
#     users_col = mongo.db.users

#     user = users_col.find_one({"email": email})
#     if not user:
#         return jsonify({"msg": "User not found"}), 404

#     join_date = datetime.strptime(user["join_date"], "%Y-%m-%d")
#     dynamic_balance = calculate_dynamic_leave_balance(join_date)

#     return jsonify({
#         "email": email,
#         "dynamic_pl_balance": dynamic_balance
#     }), 200
@leave_bp.route("/my-leave-balance", methods=["GET"])
@jwt_required()
def get_leave_balance():
    email = get_jwt_identity()
    users_col = mongo.db.users
    leave_requests = mongo.db.leave_requests

    user = users_col.find_one({"email": email})
    if not user:
        return jsonify({"msg": "User not found"}), 404

    join_date = user.get("join_date")
    if not join_date:
        return jsonify({"msg": "Join date not found"}), 400

    # 🔢 Count total leave days taken
    leaves = leave_requests.find({
        "email": email,
        "status": {"$in": ["Accepted", "Approved"]},
    })

    total_days = 0
    for leave in leaves:
        from_date = datetime.strptime(leave["from_date"], "%Y-%m-%d").date()
        to_date = datetime.strptime(leave["to_date"], "%Y-%m-%d").date()
        total_days += (to_date - from_date).days + 1

    # 💡 Compute based on complete policy
    result = calculate_dynamic_leave_balance(join_date, total_days)
    result["email"] = email

    return jsonify(result), 200



