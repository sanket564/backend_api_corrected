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
from dateutil.relativedelta import relativedelta


employee_bp = Blueprint("employee", __name__)  


# @employee_bp.route("/profile", methods=["GET"])
# @jwt_required()
# def employee_profile():
#     email = get_jwt_identity()
#     user = get_user_by_email(email)

#     if not user:
#         return jsonify({"msg": "User not found"}), 404

#     return jsonify({
#         "name": user.get("name"),
#         "email": user.get("email"),
#         "position": user.get("position"),
#         "department": user.get("department"),
#         "bloodGroup": user.get("bloodGroup"),  # ✅ added this line
#         "join_date": user.get("join_date")
#     }), 200

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
        "bloodGroup": user.get("bloodGroup"),
        "join_date": user.get("join_date"),
        "emp_code": user.get("emp_code")  # ✅ Added employee code
    }), 200




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

# @employee_bp.route("/summary", methods=["GET"])
# @jwt_required()
# def employee_summary():
#     identity = get_jwt_identity()
#     email = identity["email"] if isinstance(identity, dict) else identity
#     leave_col = mongo.db.leave_requests

#     leave_logs = list(leave_col.find({"email": email}))

#     pending_days = 0
#     accepted_days = 0

#     for leave in leave_logs:
#         from_date = leave.get("from_date")
#         to_date = leave.get("to_date")
#         status = leave.get("status")

#         if from_date and to_date:
#             try:
#                 start = datetime.strptime(from_date, "%Y-%m-%d").date()
#                 end = datetime.strptime(to_date, "%Y-%m-%d").date()
#                 num_days = (end - start).days + 1
#             except Exception:
#                 num_days = 0
#         else:
#             num_days = 0

#         if status == "Pending":
#             pending_days += num_days
#         elif status == "Accepted":
#             accepted_days += num_days

#     leaves_taken = accepted_days
#     leaves_left = max(12 - leaves_taken, 0)

#     return jsonify({
#         "leavesTaken": leaves_taken,
#         "leavesLeft": leaves_left,
#         "pendingRequests": pending_days
#     }), 200

# @employee_bp.route("/summary", methods=["GET"])
# @jwt_required()
# def employee_summary():
#     identity = get_jwt_identity()
#     email = identity["email"] if isinstance(identity, dict) else identity
#     leave_col = mongo.db.leave_requests
#     balance_col = mongo.db.leave_balance  # ✅ collection where admin stores balance

#     # 📊 Fetch all leave logs
#     leave_logs = list(leave_col.find({"email": email}))

#     pending_days = 0
#     accepted_days = 0

#     for leave in leave_logs:
#         from_date = leave.get("from_date")
#         to_date = leave.get("to_date")
#         status = leave.get("status")

#         if from_date and to_date:
#             try:
#                 start = datetime.strptime(from_date, "%Y-%m-%d").date()
#                 end = datetime.strptime(to_date, "%Y-%m-%d").date()
#                 num_days = (end - start).days + 1
#             except Exception:
#                 num_days = 0
#         else:
#             num_days = 0

#         if status == "Pending":
#             pending_days += num_days
#         elif status == "Accepted":
#             accepted_days += num_days

#     # 🔄 Fetch dynamic total from leave_balances
#     record = balance_col.find_one({"email": email})
#     total_allocated = record["balance"] if record and "balance" in record else 0

#     leaves_taken = accepted_days
#     leaves_left = max(total_allocated - leaves_taken, 0)

#     return jsonify({
#         "leavesTaken": leaves_taken,
#         "leavesLeft": leaves_left,
#         "pendingRequests": pending_days,
#         "totalAllocated": total_allocated
#     }), 200

# @employee_bp.route("/summary", methods=["GET"])
# @jwt_required()
# def employee_summary():
#     identity = get_jwt_identity()
#     email = identity["email"] if isinstance(identity, dict) else identity
#     users_col = mongo.db.users
#     leave_col = mongo.db.leave_requests

#     # Fetch user
#     user = users_col.find_one({"email": email})
#     if not user:
#         return jsonify({"msg": "User not found"}), 404

#     try:
#         join_date = datetime.strptime(user.get("join_date", ""), "%Y-%m-%d").date()
#     except Exception:
#         return jsonify({"msg": "Invalid join date format"}), 400

#     today = datetime.today().date()
#     total_allocated = 0

#     months_since_join = (today.year - join_date.year) * 12 + today.month - join_date.month

#     if months_since_join < 3:
#         # 🚦 Still in probation
#         total_allocated = months_since_join * 1
#     elif months_since_join < 12:
#         # 🌓 Post-probation, quarterly accrual
#         quarters_completed = (months_since_join - 3) // 3 + 1
#         total_allocated = quarters_completed * 5
#     else:
#         # 📅 After 1 year, 20 PLs for the calendar year
#         total_allocated = 20

#     # Fetch accepted + pending leaves
#     leave_logs = list(leave_col.find({"email": email}))

#     pending_days = 0
#     accepted_days = 0

#     for leave in leave_logs:
#         from_date = leave.get("from_date")
#         to_date = leave.get("to_date")
#         status = leave.get("status")

#         if from_date and to_date:
#             try:
#                 start = datetime.strptime(from_date, "%Y-%m-%d").date()
#                 end = datetime.strptime(to_date, "%Y-%m-%d").date()
#                 num_days = (end - start).days + 1
#             except Exception:
#                 num_days = 0
#         else:
#             num_days = 0

#         if status == "Pending":
#             pending_days += num_days
#         elif status == "Accepted":
#             accepted_days += num_days

#     leaves_taken = accepted_days
#     leaves_left = max(total_allocated - leaves_taken, 0)

#     return jsonify({
#         "leavesTaken": leaves_taken,
#         "leavesLeft": leaves_left,
#         "pendingRequests": pending_days,
#         "totalAllocated": total_allocated
#     }), 200

@employee_bp.route("/summary", methods=["GET"])
@jwt_required()
def employee_summary():
    identity = get_jwt_identity()
    email = identity["email"] if isinstance(identity, dict) else identity
    users_col = mongo.db.users
    leave_col = mongo.db.leave_requests

    # Fetch user
    user = users_col.find_one({"email": email})
    if not user:
        return jsonify({"msg": "User not found"}), 404

    try:
        join_date = datetime.strptime(user.get("join_date", ""), "%Y-%m-%d").date()
    except Exception:
        return jsonify({"msg": "Invalid join date format"}), 400

    today = datetime.today().date()
    total_allocated = 0

    months_since_join = (today.year - join_date.year) * 12 + today.month - join_date.month
    probation_end = join_date + relativedelta(months=3)

    # 📌 Step 1: Accrual Calculation
    probation_pl = min(months_since_join, 3) * 1  # 1 PL/month in probation
    post_probation_pl = 0
    annual_pl = 0

    if months_since_join >= 3:
        quarters_completed = (months_since_join - 3) // 3 + 1
        post_probation_pl = quarters_completed * 5

    if months_since_join >= 12:
        annual_pl = 20

    # 📌 Step 2: Leave Taken
    leave_logs = list(leave_col.find({"email": email, "status": {"$in": ["Accepted", "Approved"]}}))

    accepted_days = 0
    for leave in leave_logs:
        try:
            start = datetime.strptime(leave["from_date"], "%Y-%m-%d").date()
            end = datetime.strptime(leave["to_date"], "%Y-%m-%d").date()
            accepted_days += (end - start).days + 1
        except:
            pass

    # 📌 Step 3: Probation Leave Expiry Handling
    if today > probation_end:
        # Get how many leaves were taken **during probation**
        probation_taken = 0
        for leave in leave_logs:
            try:
                start = datetime.strptime(leave["from_date"], "%Y-%m-%d").date()
                end = datetime.strptime(leave["to_date"], "%Y-%m-%d").date()
                if end <= probation_end:
                    probation_taken += (end - start).days + 1
            except:
                pass

        expired_probation_pl = max(0, probation_pl - probation_taken)
    else:
        expired_probation_pl = 0

    # 📌 Step 4: Final Allocation
    total_allocated = probation_pl + post_probation_pl + annual_pl - expired_probation_pl
    leaves_left = max(total_allocated - accepted_days, 0)

    # 📌 Pending Requests
    pending_days = 0
    pending_logs = list(leave_col.find({"email": email, "status": "Pending"}))
    for leave in pending_logs:
        try:
            start = datetime.strptime(leave["from_date"], "%Y-%m-%d").date()
            end = datetime.strptime(leave["to_date"], "%Y-%m-%d").date()
            pending_days += (end - start).days + 1
        except:
            pass

    return jsonify({
        "leavesTaken": accepted_days,
        "leavesLeft": leaves_left,
        "pendingRequests": pending_days,
        "totalAllocated": total_allocated,
        "expiredProbationLeaves": expired_probation_pl
    }), 200



# @employee_bp.route("/holidays", methods=["GET"])
# @jwt_required()
# def get_employee_holidays():
#     holidays_col = mongo.db.holidays
#     holidays = list(holidays_col.find().sort("date", 1))

#     for h in holidays:
#         h["_id"] = str(h["_id"])
#     return jsonify(holidays), 200

@employee_bp.route("/holidays", methods=["GET"])
@jwt_required()
def get_employee_holidays():
    holidays_col = mongo.db.holidays
    
    # Use projection to get only 'date' and 'name'
    holidays = list(holidays_col.find({}, {"_id": 0, "date": 1, "name": 1}).sort("date", 1))

    return jsonify(holidays), 200




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
