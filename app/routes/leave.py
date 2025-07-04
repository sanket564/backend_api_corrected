from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.extensions import mongo
from bson import ObjectId
from app.utils.leave_utils import calculate_dynamic_leave_balance
from app.utils.notification_utils import create_notification
from app.utils.notifier import send_notification_email
from dateutil.relativedelta import relativedelta



leave_bp = Blueprint("leave", __name__)

@leave_bp.route("/withdraw/<leave_id>", methods=["DELETE"])
@jwt_required()
def withdraw_leave(leave_id):
    user_email = get_jwt_identity()  # This is the email from JWT

    leave_col = mongo.db.leave_requests
    leave = leave_col.find_one({"_id": ObjectId(leave_id)})

    if not leave:
        return jsonify({"error": "Leave not found"}), 404

    # ✅ Compare with email instead of employee_id
    if leave.get("email") != user_email:
        return jsonify({"error": "Unauthorized"}), 403

    leave_col.delete_one({"_id": ObjectId(leave_id)})

    return jsonify({"message": "Leave withdrawn successfully."}), 200




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

#     return jsonify({"msg": "Leave  submitted"}), 201

# @leave_bp.route("/", methods=["POST"])
# @jwt_required()
# def _leave():
#     email = get_jwt_identity()
#     leave_s = mongo.db.leave_s
#     data = .get_json()

#     from_date = data.get("from_date")
#     to_date = data.get("to_date")
#     reason = data.get("reason")

#     if not from_date or not to_date or not reason:
#         return jsonify({"msg": "From date, to date, and reason are required"}), 400

#     # Check for overlapping leave
#     existing = leave_s.find_one({
#         "email": email,
#         "$or": [
#             {"from_date": {"$lte": to_date}, "to_date": {"$gte": from_date}}
#         ]
#     })
#     if existing:
#         return jsonify({"msg": "Leave  already exists for this range"}), 409

#     leave_s.insert_one({
#         "email": email,
#         "reason": reason,
#         "from_date": from_date,
#         "to_date": to_date,
#         "status": "Pending",
#         "submitted_at": datetime.now()
#     })

#     return jsonify({"msg": "Leave  submitted"}), 201
# @leave_bp.route("/", methods=["POST"])
# @jwt_required()
# def _leave():
#     email = get_jwt_identity()
#     users_col = mongo.db.users
#     leave_s = mongo.db.leave_s
#     data = .get_json()

#     from_date = data.get("from_date")
#     to_date = data.get("to_date")
#     reason = data.get("reason")

#     if not from_date or not to_date or not reason:
#         return jsonify({"msg": "From date, to date, and reason are required"}), 400

#     # Prevent overlap
#     existing = leave_s.find_one({
#         "email": email,
#         "$or": [
#             {"from_date": {"$lte": to_date}, "to_date": {"$gte": from_date}}
#         ]
#     })
#     if existing:
#         return jsonify({"msg": "Leave request already exists for this range"}), 409

#     # Pull approvers from user profile
#     user = users_col.find_one({"email": email})
#     approver_chain = user.get("reporting_to", [])
#     current_approver = approver_chain[0] if approver_chain else None

#     leave_requests.insert_one({
#         "email": email,
#         "from_date": from_date,
#         "to_date": to_date,
#         "reason": reason,
#         "status": "Pending",
#         "approver_chain": approver_chain,
#         "current_approver": current_approver,
#         "approval_logs": [],
#         "submitted_at": datetime.now()
#     })
    
#     if current_approver:
#      create_notification(
#         current_approver,
#         f"{email} has requested leave from {from_date} to {to_date}.",
#         "action"
#     )
    
#     return jsonify({"msg": "Leave request submitted"}), 201

# @leave_bp.route("/request", methods=["POST"])
# @jwt_required()
# def request_leave():
#     email = get_jwt_identity()
#     users_col = mongo.db.users
#     leave_requests = mongo.db.leave_requests
#     data = request.get_json()

#     from_date = data.get("from_date")
#     to_date = data.get("to_date")
#     reason = data.get("reason")

#     if not from_date or not to_date or not reason:
#         return jsonify({"msg": "From date, to date, and reason are required"}), 400

#     # Prevent overlap
#     existing = leave_requests.find_one({
#         "email": email,
#         "$or": [
#             {"from_date": {"$lte": to_date}, "to_date": {"$gte": from_date}}
#         ]
#     })
#     if existing:
#         return jsonify({"msg": "Leave request already exists for this range"}), 409

#     user = users_col.find_one({"email": email})
#     approver_chain = user.get("reporting_to", [])
#     current_approver = approver_chain[0] if approver_chain else None

#     leave_requests.insert_one({
#         "email": email,
#         "from_date": from_date,
#         "to_date": to_date,
#         "reason": reason,
#         "status": "Pending",
#         "approver_chain": approver_chain,
#         "current_approver": current_approver,
#         "approval_logs": [],
#         "submitted_at": datetime.now()
#     })

#     if current_approver:
#         create_notification(
#             current_approver,
#             f"{email} has requested leave from {from_date} to {to_date}.",
#             "action"
#         )
#         send_notification_email(
#             email=current_approver,
#             subject="📝 New Leave Request",
#             body=f"{email} has requested leave from {from_date} to {to_date}. Please review in the portal.",
#             notif_type="action"
#         )

#     return jsonify({"msg": "Leave request submitted"}), 201
# @leave_bp.route("/request", methods=["POST"])
# @jwt_required()
# def request_leave():
#     email = get_jwt_identity()
#     users_col = mongo.db.users
#     leave_requests = mongo.db.leave_requests
#     data = request.get_json()

#     from_date = data.get("from_date")
#     to_date = data.get("to_date")
#     reason = data.get("reason")

#     if not from_date or not to_date or not reason:
#         return jsonify({"msg": "From date, to date, and reason are required"}), 400

#     # ✅ Calculate requested leave days
#     try:
#         start = datetime.strptime(from_date, "%Y-%m-%d").date()
#         end = datetime.strptime(to_date, "%Y-%m-%d").date()
#         requested_days = (end - start).days + 1
#         if requested_days <= 0:
#             return jsonify({"msg": "Invalid date range"}), 400
#     except Exception:
#         return jsonify({"msg": "Invalid date format"}), 400

#     # ✅ Prevent overlap
#     existing = leave_requests.find_one({
#         "email": email,
#         "$or": [
#             {"from_date": {"$lte": to_date}, "to_date": {"$gte": from_date}}
#         ]
#     })
#     if existing:
#         return jsonify({"msg": "Leave request already exists for this range"}), 409

#     # ✅ Fetch DOJ and compute total allocated
#     user = users_col.find_one({"email": email})
#     approver_chain = user.get("reporting_to", [])
#     current_approver = approver_chain[0] if approver_chain else None

#     try:
#         doj = datetime.strptime(user.get("join_date", ""), "%Y-%m-%d").date()
#     except:
#         return jsonify({"msg": "Invalid DOJ"}), 400

#     today = datetime.today().date()
#     months_since_join = (today.year - doj.year) * 12 + today.month - doj.month

#     if months_since_join < 3:
#         total_allocated = months_since_join * 1
#     elif months_since_join < 12:
#         quarters_completed = (months_since_join - 3) // 3 + 1
#         total_allocated = 3 + quarters_completed * 5
#     else:
#         total_allocated = 20

#     # ✅ Count already taken leave
#     past_leaves = leave_requests.find({
#         "email": email,
#         "status": {"$in": ["Accepted", "Approved"]}
#     })

#     taken_days = 0
#     for leave in past_leaves:
#         try:
#             f = datetime.strptime(leave["from_date"], "%Y-%m-%d").date()
#             t = datetime.strptime(leave["to_date"], "%Y-%m-%d").date()
#             taken_days += (t - f).days + 1
#         except:
#             continue

#     leaves_left = max(total_allocated - taken_days, 0)

#     if requested_days > leaves_left:
#         return jsonify({
#             "msg": f"Insufficient leave balance. You have {leaves_left} PLs left, but requested {requested_days}."
#         }), 400

#     # ✅ Insert the leave request
#     leave_requests.insert_one({
#         "email": email,
#         "from_date": from_date,
#         "to_date": to_date,
#         "reason": reason,
#         "status": "Pending",
#         "approver_chain": approver_chain,
#         "current_approver": current_approver,
#         "approval_logs": [],
#         "submitted_at": datetime.now()
#     })

#     if current_approver:
#         create_notification(
#             current_approver,
#             f"{email} has requested leave from {from_date} to {to_date}.",
#             "action"
#         )
#         send_notification_email(
#             email=current_approver,
#             subject="📝 New Leave Request",
#             body=f"{email} has requested leave from {from_date} to {to_date}. Please review in the portal.",
#             notif_type="action"
#         )

#     return jsonify({"msg": "Leave request submitted"}), 201

# @leave_bp.route("/request", methods=["POST"])
# @jwt_required()
# def request_leave():
#     email = get_jwt_identity()
#     users_col = mongo.db.users
#     leave_requests = mongo.db.leave_requests
#     leave_balances = mongo.db.leave_balances
#     data = request.get_json()

#     from_date = data.get("from_date")
#     to_date = data.get("to_date")
#     reason = data.get("reason")

#     if not from_date or not to_date or not reason:
#         return jsonify({"msg": "From date, to date, and reason are required"}), 400

#     # Prevent overlapping requests
#     existing = leave_requests.find_one({
#         "email": email,
#         "$or": [
#             {"from_date": {"$lte": to_date}, "to_date": {"$gte": from_date}}
#         ]
#     })
#     if existing:
#         return jsonify({"msg": "Leave request already exists for this range"}), 409

#     # Determine number of days
#     start = datetime.strptime(from_date, "%Y-%m-%d").date()
#     end = datetime.strptime(to_date, "%Y-%m-%d").date()
#     num_days = (end - start).days + 1

#     # Determine leave type (paid/LOP)
#     balance_rec = leave_balances.find_one({"email": email})
#     current_balance = balance_rec.get("pl_balance", 0) if balance_rec else 0

#     leave_type = "Paid" if current_balance >= num_days else "LOP"

#     user = users_col.find_one({"email": email})
#     approver_chain = user.get("reporting_to", [])
#     current_approver = approver_chain[0] if approver_chain else None

#     leave_requests.insert_one({
#         "email": email,
#         "from_date": from_date,
#         "to_date": to_date,
#         "reason": reason,
#         "status": "Pending",
#         "leave_type": leave_type,
#         "approver_chain": approver_chain,
#         "current_approver": current_approver,
#         "approval_logs": [],
#         "submitted_at": datetime.now()
#     })

#     return jsonify({"msg": "Leave request submitted"}), 201

from datetime import datetime, timedelta

def calculate_weekdays_only(start, end):
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # 0 = Monday, 4 = Friday
            count += 1
        current += timedelta(days=1)
    return count

# @leave_bp.route("/request", methods=["POST"])
# @jwt_required()
# def request_leave():
#     email = get_jwt_identity()
#     users_col = mongo.db.users
#     leave_requests = mongo.db.leave_requests
#     leave_balances = mongo.db.leave_balances
#     data = request.get_json()

#     from_date = data.get("from_date")
#     to_date = data.get("to_date")
#     reason = data.get("reason")

#     if not from_date or not to_date or not reason:
#         return jsonify({"msg": "From date, to date, and reason are required"}), 400

#     # Prevent overlapping requests
#     existing = leave_requests.find_one({
#         "email": email,
#         "$or": [
#             {"from_date": {"$lte": to_date}, "to_date": {"$gte": from_date}}
#         ]
#     })
#     if existing:
#         return jsonify({"msg": "Leave request already exists for this range"}), 409

#     # Calculate working days only (exclude weekends)
#     start = datetime.strptime(from_date, "%Y-%m-%d").date()
#     end = datetime.strptime(to_date, "%Y-%m-%d").date()
#     num_days = calculate_weekdays_only(start, end)

#     if num_days <= 0:
#         return jsonify({"msg": "No valid working days selected"}), 400

#     # Determine leave type
#     balance_rec = leave_balances.find_one({"email": email})
#     current_balance = balance_rec.get("pl_balance", 0) if balance_rec else 0
#     leave_type = "Paid" if current_balance >= num_days else "LOP"

#     user = users_col.find_one({"email": email})
#     approver_chain = user.get("reporting_to", [])
#     current_approver = approver_chain[0] if approver_chain else None

#     leave_requests.insert_one({
#         "email": email,
#         "from_date": from_date,
#         "to_date": to_date,
#         "reason": reason,
#         "status": "Pending",
#         "leave_type": leave_type,
#         "days_applied": num_days,  # ✅ Save actual leave days
#         "approver_chain": approver_chain,
#         "current_approver": current_approver,
#         "approval_logs": [],
#         "submitted_at": datetime.now()
#     })

#     return jsonify({
#         "msg": "Leave request submitted",
#         "leave_type": leave_type,
#         "days_applied": num_days
#     }), 201

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

    # Prevent overlapping requests
    existing = leave_requests.find_one({
        "email": email,
        "$or": [
            {"from_date": {"$lte": to_date}, "to_date": {"$gte": from_date}}
        ]
    })
    if existing:
        return jsonify({"msg": "Leave request already exists for this range"}), 409

    # Calculate working days only (exclude weekends)
    start = datetime.strptime(from_date, "%Y-%m-%d").date()
    end = datetime.strptime(to_date, "%Y-%m-%d").date()
    num_days = calculate_weekdays_only(start, end)

    if num_days <= 0:
        return jsonify({"msg": "No valid working days selected"}), 400

    # ✅ Fetch user and join date
    user = users_col.find_one({"email": email})
    if not user:
        return jsonify({"msg": "User not found"}), 404

    try:
        join_date = datetime.strptime(user.get("join_date", ""), "%Y-%m-%d").date()
    except:
        return jsonify({"msg": "Invalid join date format"}), 400

    today = datetime.today().date()
    months_since_join = (today.year - join_date.year) * 12 + today.month - join_date.month
    probation_end = join_date + relativedelta(months=3)

    # 📌 Step 1: Accrual
    probation_pl = min(months_since_join, 3) * 1
    post_probation_pl = (months_since_join - 3) // 3 * 5 if months_since_join >= 3 else 0
    annual_pl = 20 if months_since_join >= 12 else 0

    # 📌 Step 2: Approved leave days taken
    leave_logs = list(leave_requests.find({"email": email, "status": {"$in": ["Accepted", "Approved"]}}))
    accepted_days = 0
    probation_taken = 0

    for leave in leave_logs:
        try:
            l_start = datetime.strptime(leave["from_date"], "%Y-%m-%d").date()
            l_end = datetime.strptime(leave["to_date"], "%Y-%m-%d").date()
            days = (l_end - l_start).days + 1
            accepted_days += days
            if l_end <= probation_end:
                probation_taken += days
        except:
            pass

    expired_probation_pl = max(0, probation_pl - probation_taken) if today > probation_end else 0

    # 📌 Step 3: Available balance
    total_allocated = probation_pl + post_probation_pl + annual_pl - expired_probation_pl
    leaves_left = max(total_allocated - accepted_days, 0)

    # ✅ Determine leave type dynamically
    leave_type = "Paid" if leaves_left >= num_days else "LOP"

    # ✅ Approval chain
    approver_chain = user.get("reporting_to", [])
    current_approver = approver_chain[0] if approver_chain else None

    leave_requests.insert_one({
        "email": email,
        "from_date": from_date,
        "to_date": to_date,
        "reason": reason,
        "status": "Pending",
        "leave_type": leave_type,
        "days_applied": num_days,
        "approver_chain": approver_chain,
        "current_approver": current_approver,
        "approval_logs": [],
        "submitted_at": datetime.now()
    })

    return jsonify({
        "msg": "Leave request submitted",
        "leave_type": leave_type,
        "days_applied": num_days
    }), 201





# @leave_bp.route("/my-requests", methods=["GET"])
# @jwt_required()
# def my_leave_requests():
#     email = get_jwt_identity()
#     leave_requests = mongo.db.leave_requests
#     reqs = list(leave_requests.find({"email": email}))
#     for r in reqs:
#         r["_id"] = str(r["_id"])
#     return jsonify(reqs), 200

# @leave_bp.route("/my-requests", methods=["GET"])
# @jwt_required()
# def my_leave_requests():
#     email = get_jwt_identity()
#     leave_requests = mongo.db.leave_requests

#     reqs = list(leave_requests.find({"email": email}).sort("submitted_at", -1))
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
        r["leave_type"] = r.get("leave_type", "Paid")
    return jsonify(reqs), 200


# @leave_bp.route("/approve/<leave_id>", methods=["POST"])
# @jwt_required()
# def approve_leave(leave_id):
#     from bson import ObjectId
#     email = get_jwt_identity()
#     leave_requests = mongo.db.leave_requests
#     users_col = mongo.db.users
#     holidays_col = mongo.db.holidays

#     req = leave_requests.find_one({"_id": ObjectId(leave_id)})
#     if not req:
#         return jsonify({"msg": "Leave request not found"}), 404

#     if req["status"] != "Pending":
#         return jsonify({"msg": "Request is already resolved"}), 400

#     if req["current_approver"] != email:
#         return jsonify({"msg": "You are not authorized to approve this"}), 403

#     data = request.get_json()
#     action = data.get("action")
#     if action not in ("approve", "reject"):
#         return jsonify({"msg": "Invalid action"}), 400

#     approval_log = {
#         "by": email,
#         "status": "Approved" if action == "approve" else "Rejected",
#         "at": datetime.now()
#     }

#     update = {"$push": {"approval_logs": approval_log}}

#     if action == "reject":
#         update["$set"] = {
#             "status": "Rejected",
#             "current_approver": None,
#             "updated_at": datetime.now()
#         }
#     else:
#         chain = req.get("approver_chain", [])
#         idx = chain.index(email)

#         today_str = datetime.now().strftime("%Y-%m-%d")

#         # Find the next available approver
#         next_approver = None
#         for next_email in chain[idx + 1:]:
#             # Check if next approver is on leave
#             leave_conflict = mongo.db.leave_requests.find_one({
#                 "email": next_email,
#                 "status": "Accepted",
#                 "from_date": {"$lte": today_str},
#                 "to_date": {"$gte": today_str}
#             })

#             # Check if today is a holiday (and skip approver if it is)
#             is_holiday = holidays_col.find_one({"date": today_str})

#             if not leave_conflict and not is_holiday:
#                 next_approver = next_email
#                 break

#         if next_approver:
#             update["$set"] = {
#                 "current_approver": next_approver,
#                 "updated_at": datetime.now()
#             }
#         else:
#             update["$set"] = {
#                 "status": "Accepted",
#                 "current_approver": None,
#                 "updated_at": datetime.now()
#             }

#     leave_requests.update_one({"_id": ObjectId(leave_id)}, update)
#     create_notification(
#     req["email"],
#     f"Your leave from {req['from_date']} to {req['to_date']} was {action}d by {email}.",
#     "info"
#     )

#     return jsonify({"msg": f"Leave {action}d successfully"}), 200


# @leave_bp.route("/approve/<leave_id>", methods=["POST"])
# @jwt_required()
# def approve_leave(leave_id):
#     email = get_jwt_identity()
#     leave_requests = mongo.db.leave_requests
#     users_col = mongo.db.users
#     holidays_col = mongo.db.holidays

#     req = leave_requests.find_one({"_id": ObjectId(leave_id)})
#     if not req:
#         return jsonify({"msg": "Leave request not found"}), 404

#     if req["status"] != "Pending":
#         return jsonify({"msg": "Request is already resolved"}), 400

#     if req["current_approver"] != email:
#         return jsonify({"msg": "You are not authorized to approve this"}), 403

#     data = request.get_json()
#     action = data.get("action")
#     if action not in ("approve", "reject"):
#         return jsonify({"msg": "Invalid action"}), 400

#     approval_log = {
#         "by": email,
#         "status": "Approved" if action == "approve" else "Rejected",
#         "at": datetime.now()
#     }

#     update = {"$push": {"approval_logs": approval_log}}

#     if action == "reject":
#         update["$set"] = {
#             "status": "Rejected",
#             "current_approver": None,
#             "updated_at": datetime.now()
#         }
#     else:
#         chain = req.get("approver_chain", [])
#         idx = chain.index(email)
#         today_str = datetime.now().strftime("%Y-%m-%d")

#         next_approver = None
#         for next_email in chain[idx + 1:]:
#             leave_conflict = mongo.db.leave_requests.find_one({
#                 "email": next_email,
#                 "status": "Accepted",
#                 "from_date": {"$lte": today_str},
#                 "to_date": {"$gte": today_str}
#             })

#             is_holiday = holidays_col.find_one({"date": today_str})

#             if not leave_conflict and not is_holiday:
#                 next_approver = next_email
#                 break

#         if next_approver:
#             update["$set"] = {
#                 "current_approver": next_approver,
#                 "updated_at": datetime.now()
#             }
#         else:
#             update["$set"] = {
#                 "status": "Accepted",
#                 "current_approver": None,
#                 "updated_at": datetime.now()
#             }

#     leave_requests.update_one({"_id": ObjectId(leave_id)}, update)

#     create_notification(
#         req["email"],
#         f"Your leave from {req['from_date']} to {req['to_date']} was {action}d by {email}.",
#         "info"
#     )
#     send_notification_email(
#         email=req["email"],
#         subject=f"Your Leave Was {action.capitalize()}",
#         body=f"Hi,\n\nYour leave from {req['from_date']} to {req['to_date']} was {action}d by {email}.\n\nThank you.",
#         notif_type="info"
#     )

#     return jsonify({"msg": f"Leave {action}d successfully"}), 200

@leave_bp.route("/approve/<leave_id>", methods=["POST"])
@jwt_required()
def approve_leave(leave_id):
    email = get_jwt_identity()
    leave_requests = mongo.db.leave_requests
    leave_balances = mongo.db.leave_balances

    req = leave_requests.find_one({"_id": ObjectId(leave_id)})
    if not req:
        return jsonify({"msg": "Leave request not found"}), 404
    if req["status"] != "Pending":
        return jsonify({"msg": "Already resolved"}), 400
    if req["current_approver"] != email:
        return jsonify({"msg": "Unauthorized"}), 403

    action = request.get_json().get("action")
    if action not in ("approve", "reject"):
        return jsonify({"msg": "Invalid action"}), 400

    update = {"$push": {
        "approval_logs": {
            "by": email,
            "status": action.capitalize(),
            "at": datetime.now()
        }
    }}

    if action == "reject":
        update["$set"] = {
            "status": "Rejected",
            "current_approver": None,
            "updated_at": datetime.now()
        }
    else:
        # Final approval
        update["$set"] = {
            "status": "Accepted",
            "current_approver": None,
            "updated_at": datetime.now()
        }

        # 💰 Deduct leave if Paid
        if req.get("leave_type") == "Paid":
            num_days = (
                datetime.strptime(req["to_date"], "%Y-%m-%d").date() -
                datetime.strptime(req["from_date"], "%Y-%m-%d").date()
            ).days + 1
            leave_balances.update_one(
                {"email": req["email"]},
                {"$inc": {"pl_balance": -num_days}}
            )

    leave_requests.update_one({"_id": ObjectId(leave_id)}, update)
    return jsonify({"msg": f"Leave {action}d successfully"}), 200



# @leave_bp.route("/pending-approvals", methods=["GET"])
# @jwt_required()
# def pending_approvals():
#     email = get_jwt_identity()
#     leave_requests = mongo.db.leave_requests

#     pending = list(leave_requests.find({
#         "status": "Pending",
#         "current_approver": email
#     }).sort("submitted_at", -1))

#     for req in pending:
#         req["_id"] = str(req["_id"])
#     return jsonify(pending), 200

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
        req["leave_type"] = req.get("leave_type", "Paid")
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
# @leave_bp.route("/my-leave-balance", methods=["GET"])
# @jwt_required()
# def get_leave_balance():
#     email = get_jwt_identity()
#     users_col = mongo.db.users
#     leave_requests = mongo.db.leave_requests

#     user = users_col.find_one({"email": email})
#     if not user:
#         return jsonify({"msg": "User not found"}), 404

#     join_date = user.get("join_date")
#     if not join_date:
#         return jsonify({"msg": "Join date not found"}), 400

#     # 🔢 Count total leave days taken
#     leaves = leave_requests.find({
#         "email": email,
#         "status": {"$in": ["Accepted", "Approved"]},
#     })

#     total_days = 0
#     for leave in leaves:
#         from_date = datetime.strptime(leave["from_date"], "%Y-%m-%d").date()
#         to_date = datetime.strptime(leave["to_date"], "%Y-%m-%d").date()
#         total_days += (to_date - from_date).days + 1

#     # 💡 Compute based on complete policy
#     result = calculate_dynamic_leave_balance(join_date, total_days)
#     result["email"] = email

#     return jsonify(result), 200
@leave_bp.route("/my-leave-balance", methods=["GET"])
@jwt_required()
def get_leave_balance():
    email = get_jwt_identity()
    leave_balances = mongo.db.leave_balances

    balance = leave_balances.find_one({"email": email})
    if not balance:
        return jsonify({"msg": "No leave balance set"}), 404

    return jsonify({
        "email": email,
        "balance": balance.get("balance", 0),
        "last_updated": balance.get("updated_at")
    }), 200




