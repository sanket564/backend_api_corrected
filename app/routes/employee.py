# from flask import Blueprint, request, jsonify
# from flask_jwt_extended import jwt_required, get_jwt_identity
# from datetime import datetime, timedelta
# from ..models import user
# from app.extensions import mongo
# from ..models.user import get_user_by_email
# from pymongo import MongoClient


# employee_bp = Blueprint('employee', __name__)


# @employee_bp.route('/profile', methods=['GET'])
# @jwt_required()
# def employee_profile():
#     email = get_jwt_identity()
#     user = get_user_by_email(email)

#     if not user:
#         return jsonify({"msg": "User not found"}), 404

#     return jsonify({
#         "name": user.get("name"),
#         "email": user.get("email"),
#         "department": user.get("department"),
#         "position": user.get("position"),
#         "join_date": user.get("join_date"),
#     }), 200

# @employee_bp.route("/summary", methods=["GET"])
# @jwt_required()
# def employee_summary():
#     identity = get_jwt_identity()
#     email = identity["email"] if isinstance(identity, dict) else identity
#     leave_col = mongo.db.leave_requests

#     leave_logs = list(leave_col.find({"email": email}))
#     pending_leaves = [leave for leave in leave_logs if leave.get("status") == "Pending"]
#     accepted_leaves = [leave for leave in leave_logs if leave.get("status") == "Accepted"]

#     leaves_taken = len(accepted_leaves)
#     leaves_left = max(12 - leaves_taken, 0)

#     return jsonify({
#         "leavesTaken": leaves_taken,
#         "leavesLeft": leaves_left,
#         "pendingRequests": len(pending_leaves)
#     }), 200




from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from datetime import datetime
from app.extensions import mongo
from ..models.user import get_user_by_email

employee_bp = Blueprint("employee", __name__)  


@employee_bp.route("/profile", methods=["GET"])
@jwt_required()
def employee_profile():
    email = get_jwt_identity()
    user = get_user_by_email(email)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "name": user.get("name"),
        "email": user.get("email"),
        "position": user.get("position"),
        "department": user.get("department"),
        "bloodGroup": user.get("bloodGroup"),  # ✅ added this line
        "join_date": user.get("join_date")
    }), 200



@employee_bp.route("/summary", methods=["GET"])
@jwt_required()
def employee_summary():
    identity = get_jwt_identity()
    email = identity["email"] if isinstance(identity, dict) else identity
    leave_col = mongo.db.leave_requests

    leave_logs = list(leave_col.find({"email": email}))
    pending_leaves = [leave for leave in leave_logs if leave.get("status") == "Pending"]
    accepted_leaves = [leave for leave in leave_logs if leave.get("status") == "Accepted"]

    leaves_taken = len(accepted_leaves)
    leaves_left = max(12 - leaves_taken, 0)

    return jsonify({
        "leavesTaken": leaves_taken,
        "leavesLeft": leaves_left,
        "pendingRequests": len(pending_leaves)
    }), 200


@employee_bp.route("/update-profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user_email = get_jwt_identity()
    data = request.get_json()
    users_col = mongo.db.users

    update_data = {}
    if 'name' in data:
        update_data['name'] = data['name']
    if 'department' in data:
        update_data['department'] = data['department']
    if 'position' in data:
        update_data['position'] = data['position']
    if 'password' in data and data['password'].strip() != "":
        hashed_password = generate_password_hash(data['password'])
        update_data['password'] = hashed_password

    if not update_data:
        return jsonify({"msg": "No fields to update"}), 400

    result = users_col.update_one(
        {"email": user_email},
        {"$set": update_data}
    )

    if result.modified_count > 0:
        return jsonify({"msg": "Profile updated successfully"}), 200
    else:
        return jsonify({"msg": "No changes made"}), 200
