from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
import csv, io, os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from pytz import timezone
import dateutil.parser
from dateutil.relativedelta import relativedelta
from app.extensions import mongo
from app.utils.notification_utils import create_notification
from app.utils.notifier import send_notification_email
from datetime import datetime, timedelta
from collections import defaultdict

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/check", methods=["GET"])
def check_admin_exists():
    users_col = mongo.db.users
    exists = users_col.find_one({"role": "admin"}) is not None
    return jsonify({"exists": exists})


# @admin_bp.route("/employees/<int:EmployeeId>", methods=["GET"]
# @jwt_required()
# def get_employee_details(EmployeeId):
#     users_col = mongo.db.users
#     employees_col = mongo.db.employees

#     requester_email = get_jwt_identity()
#     admin = users_col.find_one({"email": requester_email})

#     if not admin or admin.get("role") != "admin":
#         return jsonify({"msg": "Unauthorized"}), 403

#     print(f"🔍 Looking for EmployeeId: {EmployeeId} ({type(EmployeeId)})")

#     emp = employees_col.find_one({"EmployeeId": EmployeeId})
#     if not emp:
#         return jsonify({"msg": "Employee not found"}), 404

#     emp["_id"] = str(emp["_id"])
#     return jsonify(emp), 200

@admin_bp.route("/employees/biometric", methods=["GET"])
@jwt_required()
def get_employees():
    users_col = mongo.db.users
    employee_master_col = mongo.db.employee_master

    requester_email = get_jwt_identity()
    admin = users_col.find_one({"email": requester_email})

    if not admin or admin.get("role") != "admin":
        return jsonify({"msg": "Unauthorized"}), 403

    # 🔍 Optional filter
    employee_id = request.args.get("EmployeeId")

    query = {}
    if employee_id:
        try:
            employee_id = int(employee_id)
        except ValueError:
            return jsonify({"msg": "Invalid EmployeeId"}), 400

        query["$or"] = [
            {"EmployeeId": employee_id},
            {"EmployeeId": str(employee_id)}
        ]

    employees = list(employee_master_col.find(query).sort("EmployeeId", 1))

    for emp in employees:
        emp["_id"] = str(emp["_id"])

    if employee_id and not employees:
        return jsonify({"msg": "Employee not found"}), 404

    return jsonify(employees), 200

def get_week_range(date):
    start = date - timedelta(days=date.weekday())  # Monday
    end = start + timedelta(days=6)
    return start, end


@admin_bp.route("/biometric/weekly-underworked", methods=["GET"])
@jwt_required()
def get_weekly_underworked_employees():
    attendance_col = mongo.db.biometric_logs  # or your attendance collection

    today = datetime.utcnow()
    start_of_week, end_of_week = get_week_range(today)

    # Convert to ISO format
    start_iso = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_iso = end_of_week.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Fetch attendance within the week
    records = attendance_col.find({
        "AttendanceDate": {
            "$gte": start_iso,
            "$lte": end_iso
        },
        "Status": "Present"
    })

    employee_minutes = defaultdict(int)

    for rec in records:
        emp_id = rec.get("EmployeeId")
        duration = rec.get("Duration", 0)
        employee_minutes[emp_id] += duration

    result = []
    for emp_id, total_minutes in employee_minutes.items():
        if total_minutes < 2700:  # Less than 45 hours
            result.append({
                "EmployeeId": emp_id,
                "TotalHours": round(total_minutes / 60, 2)
            })

    return jsonify(result), 200



@admin_bp.route("/recalculate-leaves", methods=["POST"])
@jwt_required()
def recalculate_leaves():
    user = mongo.db.users.find_one({"email": get_jwt_identity()})
    if not user or user.get("role") != "admin":
        return jsonify({"msg": "Unauthorized"}), 403

    update_leave_balance()
    return jsonify({"msg": "Leave balances updated successfully."}), 200

# @admin_bp.route("/employees/<emp_id>", methods=["PUT"])
# @jwt_required()
# def edit_employee(emp_id):
#     users_col = mongo.db.users
#     leave_balance = mongo.db.leave_balance

#     admin_email = get_jwt_identity()
#     admin = users_col.find_one({"email": admin_email})
#     if not admin or admin.get("role") != "admin":
#         return jsonify({"msg": "Unauthorized"}), 403

#     if not ObjectId.is_valid(emp_id):
#         return jsonify({"msg": "Invalid employee ID"}), 400

#     employee = users_col.find_one({"_id": ObjectId(emp_id)})
#     if not employee:
#         return jsonify({"msg": "Employee not found"}), 404

#     data = request.get_json()
#     update_fields = {}
#     for field in ["name", "email", "department", "position"]:
#         if field in data:
#             update_fields[field] = data[field]

#     # ✅ Handle leave balance update
#     if "leave_balance" in data:
#         leave_balance.update_one(
#             {"email": employee["email"]},
#             {
#                 "$set": {
#                     "balance": data["leave_balance"],
#                     "updated_by": admin_email,
#                     "updated_at": datetime.utcnow()
#                 }
#             },
#             upsert=True
#         )

#     create_notification(
#     target_email,
#     f"Your leave balance has been updated to {new_balance}.",
#     "info"
#     )

#     if update_fields:
#         users_col.update_one({"_id": ObjectId(emp_id)}, {"$set": update_fields})

#     return jsonify({"msg": "Employee updated successfully"}), 200


@admin_bp.route("/employees/<emp_id>", methods=["PUT"])
@jwt_required()
def edit_employee(emp_id):
    users_col = mongo.db.users
    leave_balance = mongo.db.leave_balances  # fixed collection name

    admin_email = get_jwt_identity()
    admin = users_col.find_one({"email": admin_email})
    if not admin or admin.get("role") != "admin":
        return jsonify({"msg": "Unauthorized"}), 403

    if not ObjectId.is_valid(emp_id):
        return jsonify({"msg": "Invalid employee ID"}), 400

    employee = users_col.find_one({"_id": ObjectId(emp_id)})
    if not employee:
        return jsonify({"msg": "Employee not found"}), 404

    data = request.get_json()
    update_fields = {}
    for field in ["name", "email", "department", "position"]:
        if field in data:
            update_fields[field] = data[field]

    # ✅ Handle leave balance update
    if "leave_balance" in data:
        new_balance = data["leave_balance"]
        leave_balance.update_one(
            {"email": employee["email"]},
            {
                "$set": {
                    "balance": new_balance,
                    "updated_by": admin_email,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        # ✅ Notify employee
        create_notification(
            employee["email"],
            f"Your leave balance has been updated to {new_balance}.",
            "info"
        )
        send_notification_email(
            email=employee["email"],
            subject="📊 Leave Balance Updated",
            body=f"Hi {employee['name']},\n\nYour leave balance has been updated to {new_balance} by Admin.\n\nThanks,\nHR Team",
            notif_type="info"
        )

    if update_fields:
        users_col.update_one({"_id": ObjectId(emp_id)}, {"$set": update_fields})

    return jsonify({"msg": "Employee updated successfully"}), 200




@admin_bp.route("/employees", methods=["GET"])
@jwt_required()
def get_all_employees():
    users_col = mongo.db.users

    admin_email = get_jwt_identity()
    admin = users_col.find_one({"email": admin_email})
    if not admin or admin.get("role") != "admin":
        return jsonify({"msg": "Unauthorized"}), 403

    # ✅ Include _id
    employees = list(users_col.find(
        {"role": {"$ne": "admin"}},
        {"_id": 1, "name": 1, "email": 1, "department": 1, "position": 1}
    ))

    # ✅ Convert _id to string
    for emp in employees:
        emp["_id"] = str(emp["_id"])

    return jsonify(employees), 200

# @admin_bp.route("/biometric-logs", methods=["GET"])
# @jwt_required()
# def get_biometric_logs():
#     email = get_jwt_identity()
#     users_col = mongo.db.users
#     logs_col = mongo.db.biometric_logs  # your MongoDB collection

#     # 🔐 Check if the logged-in user is an admin
#     user = users_col.find_one({"email": email})
#     if not user or user.get("role") != "admin":
#         return jsonify({"msg": "Unauthorized"}), 403

#     # 🔍 Optional Filters
#     query = {}
#     date_filter = request.args.get("date")
#     employee_id = request.args.get("employee_id")

#     if date_filter:
#         try:
#             datetime.strptime(date_filter, "%Y-%m-%d")  # Validate format
#             query["AttendanceDate"] = date_filter
#         except ValueError:
#             return jsonify({"msg": "Invalid date format. Use YYYY-MM-DD."}), 400

#     if employee_id:
#         query["EmployeeId"] = int(employee_id)

#     # 📤 Fetch and return logs
#     logs = list(logs_col.find(query).sort("AttendanceDate", -1))
#     for log in logs:
#         log["_id"] = str(log["_id"])

#     return jsonify(logs), 200

# @admin_bp.route("/biometric-logs", methods=["GET"])
# @jwt_required()
# def get_biometric_logs():
#     email = get_jwt_identity()
#     users_col = mongo.db.users
#     logs_col = mongo.db.biometric_logs  # your MongoDB collection

#     # 🔐 Check if the logged-in user is an admin
#     user = users_col.find_one({"email": email})
#     if not user or user.get("role") != "admin":
#         return jsonify({"msg": "Unauthorized"}), 403

#     # 🔍 Optional Filters
#     query = {}
#     date_filter = request.args.get("date")
#     employee_id = request.args.get("employee_id")

#     if date_filter:
#         try:
#             datetime.strptime(date_filter, "%Y-%m-%d")  # Validate format
#             query["AttendanceDate"] = date_filter
#         except ValueError:
#             return jsonify({"msg": "Invalid date format. Use YYYY-MM-DD."}), 400

#     if employee_id:
#         try:
#             query["EmployeeId"] = int(employee_id)
#         except ValueError:
#             return jsonify({"msg": "Employee ID must be an integer."}), 400

#     # 📤 Fetch and return logs
#     logs = list(logs_col.find(query).sort("AttendanceDate", -1))
#     for log in logs:
#         log["_id"] = str(log["_id"])

#         # 🔁 Convert duration from minutes to hours
#         if "Duration" in log and isinstance(log["Duration"], (int, float)):
#             log["DurationHours"] = round(log["Duration"] / 60.0, 2)

#     return jsonify(logs), 200

# @admin_bp.route("/biometric-logs", methods=["GET"])
# @jwt_required()
# def get_biometric_logs():
#     email = get_jwt_identity()
#     users_col = mongo.db.users
#     logs_col = mongo.db.biometric_logs

#     # 🔐 Admin auth check
#     user = users_col.find_one({"email": email})
#     if not user or user.get("role") != "admin":
#         return jsonify({"msg": "Unauthorized"}), 403

#     # 🔍 Optional filters
#     query = {}
#     date_filter = request.args.get("date")
#     employee_id = request.args.get("employee_id")

#     if date_filter:
#         try:
#             datetime.strptime(date_filter, "%Y-%m-%d")
#             query["AttendanceDate"] = date_filter
#         except ValueError:
#             return jsonify({"msg": "Invalid date format. Use YYYY-MM-DD."}), 400

#     if employee_id:
#         try:
#             query["EmployeeId"] = int(employee_id)
#         except ValueError:
#             return jsonify({"msg": "Employee ID must be an integer."}), 400

#     # 📥 Fetch data
#     logs = list(logs_col.find(query).sort("AttendanceDate", -1))

#     for log in logs:
#         log["_id"] = str(log["_id"])
#         duration = log.get("Duration", 0)
#         log["DurationHours"] = round(duration / 60.0, 2)

#         # 📘 Apply attendance logic
#         if duration >= 540:
#             log["AttendanceStatus"] = "Present"
#         elif duration >= 240:
#             log["AttendanceStatus"] = "Half Day Leave"
#         elif duration > 0:
#             log["AttendanceStatus"] = "Full Day Leave"
#         else:
#             log["AttendanceStatus"] = "Absent"

#     return jsonify(logs), 200

# @admin_bp.route("/biometric-logs", methods=["GET"])
# @jwt_required()
# def get_biometric_logs():
#     email = get_jwt_identity()
#     users_col = mongo.db.users
#     logs_col = mongo.db.biometric_logs

#     # 🔐 Admin auth check
#     user = users_col.find_one({"email": email})
#     if not user or user.get("role") != "admin":
#         return jsonify({"msg": "Unauthorized"}), 403

#     # 🔍 Optional filters
#     query = {}
#     date_filter = request.args.get("date")
#     employee_id = request.args.get("employee_id")

#     if date_filter:
#         try:
#             datetime.strptime(date_filter, "%Y-%m-%d")
#             query["AttendanceDate"] = date_filter
#         except ValueError:
#             return jsonify({"msg": "Invalid date format. Use YYYY-MM-DD."}), 400

#     if employee_id:
#         try:
#             query["EmployeeId"] = int(employee_id)
#         except ValueError:
#             return jsonify({"msg": "Employee ID must be an integer."}), 400

#     # 📥 Fetch data
#     logs = list(logs_col.find(query).sort("AttendanceDate", -1))

#     for log in logs:
#         log["_id"] = str(log["_id"])  # For JSON serialization
#         # 👇 Optional: convert duration to readable hours
#         if "Duration" in log and isinstance(log["Duration"], (int, float)):
#             log["DurationHours"] = round(log["Duration"] / 60.0, 2)
#         # 👇 Already stored: Status (Present, Absent, etc.)
#         # log["Status"] already exists and will be sent as-is

#     return jsonify(logs), 200

@admin_bp.route("/biometric-logs", methods=["GET"])
@jwt_required()
def get_biometric_logs():
    email = get_jwt_identity()
    users_col = mongo.db.users
    logs_col = mongo.db.biometric_logs

    # 🔐 Admin auth check
    user = users_col.find_one({"email": email})
    if not user or user.get("role") != "admin":
        return jsonify({"msg": "Unauthorized"}), 403

    # 🔍 Optional filters
    query = {}
    date_filter = request.args.get("date")
    employee_id = request.args.get("employee_id")

    if date_filter:
        try:
            target_date = datetime.strptime(date_filter, "%Y-%m-%d")
            next_date = target_date + timedelta(days=1)
            query["AttendanceDate"] = {
                "$gte": target_date,
                "$lt": next_date
            }
        except ValueError:
            return jsonify({"msg": "Invalid date format. Use YYYY-MM-DD."}), 400

    if employee_id:
        try:
            query["EmployeeId"] = int(employee_id)
        except ValueError:
            return jsonify({"msg": "Employee ID must be an integer."}), 400

    # 📥 Fetch data
    logs = list(logs_col.find(query).sort("AttendanceDate", -1))

    for log in logs:
        log["_id"] = str(log["_id"])

        # ✅ Format AttendanceDate
        if "AttendanceDate" in log:
            try:
                if isinstance(log["AttendanceDate"], str):
                    log["AttendanceDate"] = datetime.strptime(
                        log["AttendanceDate"][:10], "%Y-%m-%d"
                    ).strftime("%Y-%m-%d")
                elif isinstance(log["AttendanceDate"], datetime):
                    log["AttendanceDate"] = log["AttendanceDate"].strftime("%Y-%m-%d")
            except Exception:
                pass

        # ✅ Convert duration to readable hours
        if "Duration" in log and isinstance(log["Duration"], (int, float)):
            log["DurationHours"] = round(log["Duration"] / 60.0, 2)

    return jsonify(logs), 200





# @admin_bp.route("/edit-employee/<email>", methods=["PUT"])
# @jwt_required()
# def edit_employee(email):
#     users_col = mongo.db.users

#     admin_email = get_jwt_identity()
#     admin = users_col.find_one({"email": admin_email})
#     if not admin or admin.get("role") != "admin":
#         return jsonify({"msg": "Unauthorized"}), 403

#     employee = users_col.find_one({"email": email})
#     if not employee:
#         return jsonify({"msg": "Employee not found"}), 404

#     data = request.get_json()
#     update_fields = {}
#     for field in ["name", "email", "department", "position"]:
#         if field in data:
#             update_fields[field] = data[field]

#     if not update_fields:
#         return jsonify({"msg": "No valid fields to update"}), 400

#     users_col.update_one({"email": email}, {"$set": update_fields})
#     return jsonify({"msg": "Employee updated successfully"}), 200


# @admin_bp.route("/employees/<emp_id>", methods=["PUT"])
# @jwt_required()
# def edit_employee(emp_id):
#     users_col = mongo.db.users

#     admin_email = get_jwt_identity()
#     admin = users_col.find_one({"email": admin_email})
#     if not admin or admin.get("role") != "admin":
#         return jsonify({"msg": "Unauthorized"}), 403

#     if not ObjectId.is_valid(emp_id):
#         return jsonify({"msg": "Invalid employee ID"}), 400

#     employee = users_col.find_one({"_id": ObjectId(emp_id)})
#     if not employee:
#         return jsonify({"msg": "Employee not found"}), 404

#     data = request.get_json()
#     update_fields = {}
#     for field in ["name", "email", "department", "position"]:
#         if field in data:
#             update_fields[field] = data[field]

#     if not update_fields:
#         return jsonify({"msg": "No valid fields to update"}), 400

#     users_col.update_one({"_id": ObjectId(emp_id)}, {"$set": update_fields})
#     return jsonify({"msg": "Employee updated successfully"}), 200

@admin_bp.route("/employees/<emp_id>", methods=["DELETE"])
@jwt_required()
def delete_employee(emp_id):
    users_col = mongo.db.users

    admin_email = get_jwt_identity()
    admin = users_col.find_one({"email": admin_email})
    if not admin or admin.get("role") != "admin":
        return jsonify({"msg": "Unauthorized"}), 403

    if not ObjectId.is_valid(emp_id):
        return jsonify({"msg": "Invalid employee ID"}), 400

    result = users_col.delete_one({"_id": ObjectId(emp_id)})

    if result.deleted_count == 0:
        return jsonify({"msg": "Employee not found or already deleted"}), 404

    return jsonify({"msg": "Employee deleted successfully"}), 200





# @admin_bp.route("/checkins/pending", methods=["GET"])
# @jwt_required()
# def get_pending_checkins():
#     users_col = mongo.db.users
#     pending_checkins_col = mongo.db.pending_checkins

#     email = get_jwt_identity()
#     if not users_col.find_one({"email": email, "role": "admin"}):
#         return jsonify({"msg": "Unauthorized"}), 403

#     pending = list(pending_checkins_col.find({"status": "Pending"}))
#     for p in pending:
#         p["_id"] = str(p["_id"])
#         if p.get("requested_at"):
#             p["checkin_time"] = p["requested_at"].strftime("%I:%M %p")
#     return jsonify(pending), 200

# @admin_bp.route("/checkins/pending", methods=["GET"])
# @jwt_required()
# def get_pending_checkins():
#     users_col = mongo.db.users
#     pending_checkins_col = mongo.db.pending_checkins
#     india = timezone("Asia/Kolkata")

#     email = get_jwt_identity()
#     if not users_col.find_one({"email": email, "role": "admin"}):
#         return jsonify({"msg": "Unauthorized"}), 403

#     pending = list(pending_checkins_col.find({"status": "Pending"}))
#     for p in pending:
#         p["_id"] = str(p["_id"])
#         if p.get("requested_at"):
#             ist_time = p["requested_at"].astimezone(india)
#             p["checkin_time"] = ist_time.strftime("%I:%M %p")
#     return jsonify(pending), 200

@admin_bp.route("/checkins/pending", methods=["GET"])
@jwt_required()
def get_pending_checkins():
    users_col = mongo.db.users
    pending_checkins_col = mongo.db.pending_checkins

    email = get_jwt_identity()
    admin = users_col.find_one({"email": email})
    if not admin or admin["role"] != "admin":
        return jsonify({"msg": "Unauthorized"}), 403

    pending = list(pending_checkins_col.find({"status": "Pending"}))
    for p in pending:
        p["_id"] = str(p["_id"])
        # p["checkin_time"] = p["requested_at"].strftime("%I:%M %p") if p.get("requested_at") else "—"
        india = timezone("Asia/Kolkata")
        ist_time = p["requested_at"].astimezone(india)
        p["checkin_time"] = ist_time.strftime("%I:%M %p")

    print("✅ Sent to frontend:")
    from pprint import pprint
    pprint(pending)

    return jsonify(pending), 200

@admin_bp.route("/upload-biometric-logs", methods=["POST"])
@jwt_required()
def upload_biometric_logs():
    logs = request.get_json()

    if not logs or not isinstance(logs, list):
        return jsonify({"msg": "Invalid log format"}), 400

    try:
        mongo.db.biometric_logs.insert_many(logs)
        return jsonify({"msg": f"{len(logs)} logs uploaded"}), 200
    except Exception as e:
        return jsonify({"msg": "Insert failed", "error": str(e)}), 500



# @admin_bp.route("/checkins/approve/<checkin_id>", methods=["POST"])
# @jwt_required()
# def approve_checkin(checkin_id):
#     users_col = mongo.db.users
#     logs_col = mongo.db.logs
#     pending_checkins_col = mongo.db.pending_checkins

#     email = get_jwt_identity()
#     if not users_col.find_one({"email": email, "role": "admin"}):
#         return jsonify({"msg": "Unauthorized"}), 403

#     checkin = pending_checkins_col.find_one({"_id": ObjectId(checkin_id)})
#     if not checkin:
#         return jsonify({"msg": "Check-in request not found"}), 404

#     if logs_col.find_one({"email": checkin["email"], "date": checkin["date"]}):
#         return jsonify({"msg": "Check-in already exists"}), 400

#     logs_col.insert_one({
#         "email": checkin["email"],
#         "date": checkin["date"],
#         "checkin": checkin["requested_at"].strftime("%H:%M"),
#         "checkout": None,
#         "approved": True
#     })

#     pending_checkins_col.update_one({"_id": checkin["_id"]}, {"$set": {"status": "Approved"}})
#     return jsonify({"msg": "Check-in approved"}), 200

# @admin_bp.route("/checkins/approve/<checkin_id>", methods=["POST"])
# @jwt_required()
# def approve_checkin(checkin_id):
#     users_col = mongo.db.users
#     logs_col = mongo.db.logs
#     pending_checkins_col = mongo.db.pending_checkins
#     india = timezone("Asia/Kolkata")

#     email = get_jwt_identity()
#     if not users_col.find_one({"email": email, "role": "admin"}):
#         return jsonify({"msg": "Unauthorized"}), 403

#     checkin = pending_checkins_col.find_one({"_id": ObjectId(checkin_id)})
#     if not checkin:
#         return jsonify({"msg": "Check-in request not found"}), 404

#     if logs_col.find_one({"email": checkin["email"], "date": checkin["date"]}):
#         return jsonify({"msg": "Check-in already exists"}), 400

#     # Convert UTC to IST for checkin time
#     checkin_time_ist = checkin["requested_at"].astimezone(india).strftime("%H:%M")

#     logs_col.insert_one({
#         "email": checkin["email"],
#         "date": checkin["date"],  # this is already in IST format
#         "checkin": checkin_time_ist,
#         "checkout": None,
#         "approved": True
#     })

#     pending_checkins_col.update_one(
#         {"_id": checkin["_id"]},
#         {"$set": {"status": "Approved"}}
#     )

#     return jsonify({"msg": "Check-in approved"}), 200

# @admin_bp.route("/checkins/approve/<checkin_id>", methods=["POST"])
# @jwt_required()
# def approve_checkin(checkin_id):
#     users_col = mongo.db.users
#     logs_col = mongo.db.logs
#     pending_checkins_col = mongo.db.pending_checkins

#     email = get_jwt_identity()
#     if not users_col.find_one({"email": email, "role": "admin"}):
#         return jsonify({"msg": "Unauthorized"}), 403

#     checkin = pending_checkins_col.find_one({"_id": ObjectId(checkin_id)})
#     if not checkin:
#         return jsonify({"msg": "Check-in request not found"}), 404

#     if logs_col.find_one({"email": checkin["email"], "date": checkin["date"]}):
#         return jsonify({"msg": "Check-in already exists"}), 400

#     # ✅ Save checkin as UTC datetime instead of string
#     logs_col.insert_one({
#         "email": checkin["email"],
#         "date": checkin["date"],
#         "checkin": checkin["requested_at"],  # already UTC datetime
#         "checkout": None,
#         "approved": True
#     })

#     pending_checkins_col.update_one({"_id": checkin["_id"]}, {"$set": {"status": "Approved"}})
#     return jsonify({"msg": "Check-in approved"}), 200

# @admin_bp.route("/checkins/approve/<checkin_id>", methods=["POST"])
# @jwt_required()
# def approve_checkin(checkin_id):
#     users_col = mongo.db.users
#     pending_checkins_col = mongo.db.pending_checkins
#     logs_col = mongo.db.logs

#     email = get_jwt_identity()
#     admin = users_col.find_one({"email": email})
#     if not admin or admin["role"] != "admin":
#         return jsonify({"msg": "Unauthorized"}), 403

#     checkin = pending_checkins_col.find_one({"_id": ObjectId(checkin_id)})
#     if not checkin:
#         return jsonify({"msg": "Check-in request not found"}), 404

#     checkin_dt = checkin.get("requested_at")
#     if not checkin_dt:
#         return jsonify({"msg": "Invalid check-in time"}), 400

#     date_str = checkin["date"]
#     time_str = checkin_dt.strftime("%H:%M")  # Save time in 24-hour format

#     existing = logs_col.find_one({"email": checkin["email"], "date": date_str})
#     if existing:
#         return jsonify({"msg": "Employee already has a check-in for this date"}), 400

#     logs_col.insert_one({
#         "email": checkin["email"],
#         "date": date_str,
#         "checkin": time_str,
#         "checkout": None,
#         "approved": True
#     })

#     pending_checkins_col.update_one(
#         {"_id": ObjectId(checkin_id)},
#         {"$set": {"status": "Approved"}}
#     )

#     return jsonify({"msg": "Check-in approved successfully."}), 200

# @admin_bp.route("/checkins/approve/<checkin_id>", methods=["POST"])
# @jwt_required()
# def approve_checkin(checkin_id):
#     users_col = mongo.db.users
#     pending_checkins_col = mongo.db.pending_checkins
#     logs_col = mongo.db.logs

#     email = get_jwt_identity()
#     admin = users_col.find_one({"email": email})
#     if not admin or admin["role"] != "admin":
#         return jsonify({"msg": "Unauthorized"}), 403

#     checkin = pending_checkins_col.find_one({"_id": ObjectId(checkin_id)})
#     if not checkin:
#         return jsonify({"msg": "Check-in request not found"}), 404

#     checkin_dt = checkin.get("requested_at")
#     if not checkin_dt:
#         return jsonify({"msg": "Invalid check-in time"}), 400

#     date_str = checkin["date"]

#     existing = logs_col.find_one({"email": checkin["email"], "date": date_str})
#     if existing:
#         return jsonify({"msg": "Employee already has a check-in for this date"}), 400

#     logs_col.insert_one({
#         "email": checkin["email"],
#         "date": date_str,
#         "checkin": checkin_dt,  # ✅ Store full UTC datetime
#         "checkout": None,
#         "approved": True
#     })

#     pending_checkins_col.update_one(
#         {"_id": ObjectId(checkin_id)},
#         {"$set": {"status": "Approved"}}
#     )

#     return jsonify({"msg": "Check-in approved successfully."}), 200

@admin_bp.route("/checkins/approve/<checkin_id>", methods=["POST"])
@jwt_required()
def admin_approve_checkin(checkin_id):
    users_col = mongo.db.users
    pending_checkins_col = mongo.db.pending_checkins
    logs_col = mongo.db.logs

    email = get_jwt_identity()
    admin = users_col.find_one({"email": email})
    if not admin or admin["role"] != "admin":
        return jsonify({"msg": "Unauthorized"}), 403

    checkin = pending_checkins_col.find_one({"_id": ObjectId(checkin_id)})
    if not checkin:
        return jsonify({"msg": "Check-in request not found"}), 404

    date_str = checkin["date"]
    existing = logs_col.find_one({"email": checkin["email"], "date": date_str})
    if existing:
        return jsonify({"msg": "Check-in already exists"}), 400

    logs_col.insert_one({
        "email": checkin["email"],
        "date": date_str,
        "checkin": checkin["requested_at"],
        "checkout": None,
        "approved": True
    })

    pending_checkins_col.update_one(
        {"_id": ObjectId(checkin_id)},
        {"$set": {"status": "Approved"}}
    )

    return jsonify({"msg": "Admin approved check-in"}), 200


# @admin_bp.route("/checkins/reject/<checkin_id>", methods=["POST"])
# @jwt_required()
# def reject_checkin(checkin_id):
#     users_col = mongo.db.users
#     pending_checkins_col = mongo.db.pending_checkins

#     email = get_jwt_identity()
#     admin = users_col.find_one({"email": email})
#     if not admin or admin["role"] != "admin":
#         return jsonify({"msg": "Unauthorized"}), 403

#     checkin = pending_checkins_col.find_one({"_id": ObjectId(checkin_id)})
#     if not checkin:
#         return jsonify({"msg": "Check-in request not found"}), 404

#     if checkin.get("status") == "Rejected":
#         return jsonify({"msg": "Check-in request is already rejected"}), 400

#     pending_checkins_col.update_one(
#         {"_id": ObjectId(checkin_id)},
#         {"$set": {"status": "Rejected"}}
#     )

#     return jsonify({"msg": "Check-in rejected successfully."}), 200

@admin_bp.route("/checkins/reject/<checkin_id>", methods=["POST"])
@jwt_required()
def admin_reject_checkin(checkin_id):
    users_col = mongo.db.users
    pending_checkins_col = mongo.db.pending_checkins

    email = get_jwt_identity()
    admin = users_col.find_one({"email": email})
    if not admin or admin["role"] != "admin":
        return jsonify({"msg": "Unauthorized"}), 403

    checkin = pending_checkins_col.find_one({"_id": ObjectId(checkin_id)})
    if not checkin:
        return jsonify({"msg": "Check-in not found"}), 404

    pending_checkins_col.update_one(
        {"_id": ObjectId(checkin_id)},
        {"$set": {"status": "Rejected"}}
    )

    return jsonify({"msg": "Admin rejected check-in"}), 200




# @admin_bp.route("/records", methods=["GET"])
# @jwt_required()
# def all_attendance():
#     logs_col = mongo.db.logs
#     query = {}
#     email = request.args.get('email')
#     date = request.args.get('date')
#     if email:
#         query['email'] = email
#     if date:
#         query['date'] = date

#     records = list(logs_col.find(query))
#     for r in records:
#         r["_id"] = str(r["_id"])
#         india = timezone("Asia/Kolkata")
#         for k in ("checkin", "checkout"):
#             if isinstance(r.get(k), datetime):
#                 r[k] = r[k].astimezone(india).strftime("%I:%M %p")
#         # for k in ("checkin", "checkout"):
#         #     if isinstance(r.get(k), datetime):
#         #         r[k] = r[k].strftime("%I:%M %p")
#     return jsonify(records), 200

# @admin_bp.route("/records", methods=["GET"])
# @jwt_required()
# def all_attendance():
#     logs_col = mongo.db.logs
#     query = {}

#     email = request.args.get('email')
#     date = request.args.get('date')

#     if email:
#         query['email'] = email
#     if date:
#         query['date'] = date

#     records = list(logs_col.find(query))
#     india = timezone("Asia/Kolkata")

#     for r in records:
#         r["_id"] = str(r["_id"])
#         checkin = r.get("checkin")
#         checkout = r.get("checkout")

#         # Convert and format checkin/checkout
#         if isinstance(checkin, datetime):
#             checkin_local = checkin.astimezone(india)
#             r["checkin"] = checkin_local.strftime("%I:%M %p")
#         else:
#             checkin_local = None

#         if isinstance(checkout, datetime):
#             checkout_local = checkout.astimezone(india)
#             r["checkout"] = checkout_local.strftime("%I:%M %p")
#         else:
#             checkout_local = None

#         # Calculate hours worked
#         if checkin_local and checkout_local:
#             delta = checkout_local - checkin_local
#             total_hours = round(delta.total_seconds() / 3600, 2)  # e.g., 8.75
#             r["hours_worked"] = total_hours
#         else:
#             r["hours_worked"] = None

#     return jsonify(records), 200

@admin_bp.route("/records", methods=["GET"])
@jwt_required()
def all_attendance():
    logs_col = mongo.db.logs
    query = {}

    email = request.args.get('email')
    date = request.args.get('date')

    if email:
        query['email'] = email
    if date:
        query['date'] = date

    records = list(logs_col.find(query))
    india = timezone("Asia/Kolkata")

    for r in records:
        r["_id"] = str(r["_id"])
        checkin = r.get("checkin")
        checkout = r.get("checkout")

        checkin_dt, checkout_dt = None, None

        # Convert string or datetime to aware datetime
        try:
            if isinstance(checkin, str):
                checkin_dt = dateutil.parser.parse(checkin)
            elif isinstance(checkin, datetime):
                checkin_dt = checkin

            if isinstance(checkout, str):
                checkout_dt = dateutil.parser.parse(checkout)
            elif isinstance(checkout, datetime):
                checkout_dt = checkout

            # Localize
            if checkin_dt:
                checkin_dt = checkin_dt.astimezone(india)
                r["checkin"] = checkin_dt.strftime("%I:%M %p")
            if checkout_dt:
                checkout_dt = checkout_dt.astimezone(india)
                r["checkout"] = checkout_dt.strftime("%I:%M %p")

            # Calculate hours
            if checkin_dt and checkout_dt:
                total_hours = round((checkout_dt - checkin_dt).total_seconds() / 3600, 2)
                r["hours_worked"] = total_hours
            else:
                r["hours_worked"] = None
        except Exception as e:
            # In case of parsing errors
            r["hours_worked"] = None

    return jsonify(records), 200



# @admin_bp.route("/export", methods=["GET"])
# @jwt_required()
# def export_attendance():
#     logs_col = mongo.db.logs
#     query = {}
#     email = request.args.get('email')
#     date = request.args.get('date')
#     if email:
#         query['email'] = {'$regex': f'^{email}$', '$options': 'i'}
#     if date:
#         query['date'] = date

#     records = list(logs_col.find(query))
#     if not records:
#         return jsonify({"msg": "No records found"}), 404

#     output = io.StringIO()
#     writer = csv.writer(output)
#     writer.writerow(["Email", "Date", "Check-In", "Check-Out"])

#     for r in records:
#         writer.writerow([
#             r.get("email"),
#             r.get("date"),
#             r.get("checkin") if isinstance(r.get("checkin"), str)
#             else r["checkin"].strftime("%I:%M %p") if r.get("checkin") else "",
#             r.get("checkout") if isinstance(r.get("checkout"), str)
#             else r["checkout"].strftime("%I:%M %p") if r.get("checkout") else ""
#         ])
#     output.seek(0)
#     return Response(output.getvalue(), mimetype="text/csv",
#                     headers={"Content-Disposition": "attachment; filename=attendance.csv"})
@admin_bp.route("/export", methods=["GET"])
@jwt_required()
def export_attendance():
    logs_col = mongo.db.logs
    query = {}

    email = request.args.get('email')
    date = request.args.get('date')
    if email:
        query['email'] = {'$regex': f'^{email}$', '$options': 'i'}
    if date:
        query['date'] = date

    records = list(logs_col.find(query))
    if not records:
        return jsonify({"msg": "No records found"}), 404

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Email", "Date", "Check-In", "Check-Out", "Hours Worked", "Status"])

    india = timezone("Asia/Kolkata")

    for r in records:
        # Extract & format times
        checkin = r.get("checkin")
        checkout = r.get("checkout")
        hours = r.get("hours_worked")

        if isinstance(checkin, str):
            checkin_str = checkin
        elif isinstance(checkin, datetime):
            checkin = checkin.astimezone(india)
            checkin_str = checkin.strftime("%I:%M %p")
        else:
            checkin_str = ""

        if isinstance(checkout, str):
            checkout_str = checkout
        elif isinstance(checkout, datetime):
            checkout = checkout.astimezone(india)
            checkout_str = checkout.strftime("%I:%M %p")
        else:
            checkout_str = ""

        # Compute hours if needed
        if hours is None and isinstance(checkin, datetime) and isinstance(checkout, datetime):
            try:
                hours = round((checkout - checkin).total_seconds() / 3600, 2)
            except:
                hours = None

        # Determine status
        if hours is None:
            status = "Full-Day Leave"
        elif hours >= 9:
            status = "Present"
        elif hours >= 4:
            status = "Half-Day Leave"
        else:
            status = "Full-Day Leave"

        writer.writerow([
            r.get("email"),
            r.get("date"),
            checkin_str,
            checkout_str,
            hours if hours is not None else "",
            status
        ])

    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=attendance.csv"})




UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
@admin_bp.route("/upload-attendance", methods=["POST"])
@jwt_required()
def upload_attendance():
    logs_col = mongo.db.logs
    file = request.files.get('file')
    if not file:
        return jsonify({"msg": "No file uploaded"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join("uploads", filename)
    file.save(filepath)  # Save temporarily

    entries = []
    try:
        if filename.endswith(".csv"):
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entry = {
                        "email": row["email"].strip(),
                        "date": row["date"].strip(),
                        "checkin": datetime.strptime(row["checkin"], "%I:%M %p") if row["checkin"] else None,
                        "checkout": datetime.strptime(row["checkout"], "%I:%M %p") if row["checkout"] else None
                    }
                    entries.append(entry)

        elif filename.endswith(".xlsx"):
            df = pd.read_excel(filepath)
            for _, row in df.iterrows():
                entry = {
                    "email": str(row["email"]).strip(),
                    "date": str(row["date"]).strip(),
                    "checkin": datetime.strptime(row["checkin"], "%I:%M %p") if pd.notna(row["checkin"]) else None,
                    "checkout": datetime.strptime(row["checkout"], "%I:%M %p") if pd.notna(row["checkout"]) else None
                }
                entries.append(entry)
        else:
            return jsonify({"msg": "Unsupported file type"}), 400

        if entries:
            logs_col.insert_many(entries)

    except Exception as e:
        print("Error processing file:", e)
        return jsonify({"msg": "Failed to process file"}), 500
    finally:
        os.remove(filepath)

    return jsonify({"msg": "Attendance uploaded and processed successfully"}), 200

# @admin_bp.route("/total-employees", methods=["GET"])
# @jwt_required()
# def total_employees():
#     users_col = mongo.db.users
#     count = users_col.count_documents({})
#     return jsonify({"total_employees": count}), 200

# @admin_bp.route("/add-employee", methods=["POST"])
# @jwt_required()
# def add_employee():
#     users_col = mongo.db.users
#     data = request.get_json()
#     required = ("name", "email", "password", "doj")
#     if not all(k in data for k in required):
#         return jsonify({"msg": "Missing required fields"}), 400

#     if users_col.find_one({"email": data["email"]}):
#         return jsonify({"msg": "Employee already exists"}), 409
    
#     hashed_password = generate_password_hash(data["password"])


#     users_col.insert_one({
#         "name": data["name"],
#         "email": data["email"],
#         "password": hashed_password, # Ideally hash this
#         "role": "employee",
#         "join_date": data["doj"],
#         "department": data.get("department", "Not Assigned"),
#         "position": data.get("position", "Not Assigned")
#     })
#     return jsonify({"msg": "Employee added successfully"}), 201

# @admin_bp.route("/add-employee", methods=["POST"])
# @jwt_required()
# def add_employee():
#     users_col = mongo.db.users
#     data = request.get_json()
#     required = ("name", "email", "password", "join_date")
    
#     if not all(k in data for k in required):
#         return jsonify({"msg": "Missing required fields"}), 400

#     if users_col.find_one({"email": data["email"]}):
#         return jsonify({"msg": "Employee already exists"}), 409
    
#     hashed_password = generate_password_hash(data["password"])

#     users_col.insert_one({
#         "name": data["name"],
#         "email": data["email"],
#         "password": hashed_password,
#         "role": "employee",
#         "join_date": data["join_date"],
#         "department": data.get("department", "Not Assigned"),
#         "position": data.get("position", "Not Assigned"),
#         "bloodGroup": data.get("bloodGroup", "Not Provided")  # Added field
#     })
    
#     return jsonify({"msg": "Employee added successfully"}), 201


# @admin_bp.route("/add-employee", methods=["POST"])
# @jwt_required()
# def add_employee():
#     users_col = mongo.db.users
#     data = request.get_json()

#     reporting_to = data.get("reporting_to", [])  # List of emails
#     proxy_approver = data.get("proxy_approver", None)
#     role = data.get("role", "employee")  # 🔄 default to employee if not provided

#     # --- 1. Validate required fields ----------------------------------------
#     required = ("name", "email", "password", "join_date", "emp_code")
#     if not all(k in data for k in required):
#         return jsonify({"msg": "Missing required fields"}), 400

#     # --- 2. Uniqueness checks ----------------------------------------------
#     if users_col.find_one({"email": data["email"]}):
#         return jsonify({"msg": "Email already exists"}), 409

#     if users_col.find_one({"emp_code": data["emp_code"]}):
#         return jsonify({"msg": "Employee code already exists"}), 409

#     # --- 3. Insert employee -------------------------------------------------
#     hashed_password = generate_password_hash(data["password"])

#     users_col.insert_one({
#         "name": data["name"],
#         "email": data["email"],
#         "password": hashed_password,
#         "role": role,  # ✅ Use role from frontend
#         "join_date": data["join_date"],
#         "emp_code": data["emp_code"],
#         "department": data.get("department", "Not Assigned"),
#         "position": data.get("position", "Not Assigned"),
#         "bloodGroup": data.get("bloodGroup", "Not Provided"),
#         "reporting_to": reporting_to,
#         "proxy_approver": proxy_approver
#     })

#     return jsonify({"msg": f"{role.capitalize()} added successfully"}), 201



# @admin_bp.route("/add-employee", methods=["POST"])
# @jwt_required()
# def add_employee():
#     users_col = mongo.db.users
#     leave_balances_col = mongo.db.leave_balances  # ✅ New collection
#     data = request.get_json()

#     reporting_to = data.get("reporting_to", [])
#     proxy_approver = data.get("proxy_approver", None)
#     role = data.get("role", "employee")

#     required = ("name", "email", "password", "join_date", "emp_code")
#     if not all(k in data for k in required):
#         return jsonify({"msg": "Missing required fields"}), 400

#     if users_col.find_one({"email": data["email"]}):
#         return jsonify({"msg": "Email already exists"}), 409

#     if users_col.find_one({"emp_code": data["emp_code"]}):
#         return jsonify({"msg": "Employee code already exists"}), 409

#     hashed_password = generate_password_hash(data["password"])

#     # --- Insert into users collection ---
#     users_col.insert_one({
#         "name": data["name"],
#         "email": data["email"],
#         "password": hashed_password,
#         "role": role,
#         "join_date": data["join_date"],
#         "emp_code": data["emp_code"],
#         "department": data.get("department", "Not Assigned"),
#         "position": data.get("position", "Not Assigned"),
#         "bloodGroup": data.get("bloodGroup", "Not Provided"),
#         "reporting_to": reporting_to,
#         "proxy_approver": proxy_approver
#     })

#     create_notification(
#     data["email"],
#     "You have been added to the system. Please log in to view your profile.",
#     "info"
#     )


#     # --- Insert into leave_balances collection ---
#     try:
#         join_date = datetime.strptime(data["join_date"], "%Y-%m-%d")
#         probation_end = join_date + relativedelta(months=3)
#     except Exception as e:
#         return jsonify({"msg": f"Invalid join_date format. Expected YYYY-MM-DD. Error: {str(e)}"}), 400

#     leave_balances_col.insert_one({
#         "email": data["email"],
#         "join_date": join_date,
#         "probation_end": probation_end,
#         "pl_balance": 0,
#         "last_updated": datetime.now()
#     })

#     return jsonify({"msg": f"{role.capitalize()} added successfully"}), 201


from app.utils.notifier import send_notification_email  # ✅ make sure this is imported

# @admin_bp.route("/add-employee", methods=["POST"])
# @jwt_required()
# def add_employee():
#     users_col = mongo.db.users
#     leave_balances_col = mongo.db.leave_balances
#     data = request.get_json()

#     reporting_to = data.get("reporting_to", [])
#     proxy_approver = data.get("proxy_approver", None)
#     role = data.get("role", "employee")

#     required = ("name", "email", "password", "join_date", "emp_code")
#     if not all(k in data for k in required):
#         return jsonify({"msg": "Missing required fields"}), 400

#     if users_col.find_one({"email": data["email"]}):
#         return jsonify({"msg": "Email already exists"}), 409

#     if users_col.find_one({"emp_code": data["emp_code"]}):
#         return jsonify({"msg": "Employee code already exists"}), 409

#     # 📌 Plain password before hashing
#     plain_password = data["password"]
#     hashed_password = generate_password_hash(plain_password)

#     users_col.insert_one({
#         "name": data["name"],
#         "email": data["email"],
#         "password": hashed_password,
#         "role": role,
#         "join_date": data["join_date"],
#         "emp_code": data["emp_code"],
#         "department": data.get("department", "Not Assigned"),
#         "position": data.get("position", "Not Assigned"),
#         "bloodGroup": data.get("bloodGroup", "Not Provided"),
#         "reporting_to": reporting_to,
#         "proxy_approver": proxy_approver
#     })

#     # 🎯 Send welcome email to employee
#     employee_name = data["name"]
#     employee_email = data["email"]

#     email_body = f"""Hi {employee_name},

# Kindly use the below URL to access the Attendance and Leave Management System using the provided credentials.

# 🔗 URL: https://attendance-frontend-woad.vercel.app  
# 📧 Email ID: {employee_email}  
# 🔐 Password: {plain_password}

# Thanks,  
# HR Team
# """

#     send_notification_email(
#         email=employee_email,
#         subject="🎉 Welcome to the Attendance Management System",
#         body=email_body,
#         notif_type="info"
#     )

#     # 🎯 Set initial leave balance
#     try:
#         join_date = datetime.strptime(data["join_date"], "%Y-%m-%d")
#         probation_end = join_date + relativedelta(months=3)
#     except Exception as e:
#         return jsonify({"msg": f"Invalid join_date format. Expected YYYY-MM-DD. Error: {str(e)}"}), 400

#     leave_balances_col.insert_one({
#         "email": employee_email,
#         "join_date": join_date,
#         "probation_end": probation_end,
#         "pl_balance": 0,
#         "last_updated": datetime.now()
#     })

#     return jsonify({"msg": f"{role.capitalize()} added successfully"}), 201

@admin_bp.route("/add-employee", methods=["POST"])
@jwt_required()
def add_employee():
    users_col = mongo.db.users
    leave_balances_col = mongo.db.leave_balances
    data = request.get_json()

    reporting_to = data.get("reporting_to", [])
    proxy_approver = data.get("proxy_approver", None)
    role = data.get("role", "employee")

    required = ("name", "email", "password", "join_date", "emp_code")
    if not all(k in data for k in required):
        return jsonify({"msg": "Missing required fields"}), 400

    if users_col.find_one({"email": data["email"]}):
        return jsonify({"msg": "Email already exists"}), 409

    if users_col.find_one({"emp_code": data["emp_code"]}):
        return jsonify({"msg": "Employee code already exists"}), 409

    plain_password = data["password"]
    hashed_password = generate_password_hash(plain_password)

    users_col.insert_one({
        "name": data["name"],
        "email": data["email"],
        "password": hashed_password,
        "role": role,
        "join_date": data["join_date"],
        "emp_code": data["emp_code"],
        "department": data.get("department", "Not Assigned"),
        "position": data.get("position", "Not Assigned"),
        "bloodGroup": data.get("bloodGroup", "Not Provided"),
        "reporting_to": reporting_to,
        "proxy_approver": proxy_approver
    })

    # ✅ Send long welcome email
    employee_name = data["name"]
    employee_email = data["email"]

    email_body = f"""Hi {employee_name},

Welcome to the team!

We are excited to have you on board and look forward to your contributions. To help you get started smoothly, we have created your account on our Attendance and Leave Management System.

This platform is designed to manage your daily attendance, leave applications, approvals, and view your leave balance — all in one place.

You can access the system using the credentials provided below:

Login URL: https://attendance-frontend-woad.vercel.app
Login Email ID: {employee_email}
Login Password: {plain_password}

Please log in using the above details.

Key Features of the Portal:
- View and track your daily attendance
- Submit leave requests online
- Get real-time notifications on approval/rejection
- Access your leave history and balance
- Stay informed with in-app alerts and email notifications

If you face any issues while accessing the portal or have any questions, feel free to reach out to the HR team at sanket.b@otomeyt.ai or contact your reporting manager.

Once again, welcome aboard!
We wish you a successful and rewarding journey with us.

Warm regards,  
HR Team
Otomeyt AI
"""

    send_notification_email(
        email=employee_email,
        subject="🎉 Welcome to the Oto-Attendance",
        body=email_body,
        notif_type="info"
    )

    # ✅ Set leave balance
    try:
        join_date = datetime.strptime(data["join_date"], "%Y-%m-%d")
        probation_end = join_date + relativedelta(months=3)
    except Exception as e:
        return jsonify({"msg": f"Invalid join_date format. Expected YYYY-MM-DD. Error: {str(e)}"}), 400

    leave_balances_col.insert_one({
        "email": employee_email,
        "join_date": join_date,
        "probation_end": probation_end,
        "pl_balance": 0,
        "last_updated": datetime.now()
    })

    return jsonify({"msg": f"{role.capitalize()} added successfully"}), 201





@admin_bp.route("/leave-requests", methods=["GET"])
@jwt_required()
def view_leave_requests():
    users_col = mongo.db.users
    leave_requests_col = mongo.db.leave_requests

    email = get_jwt_identity()
    user = users_col.find_one({"email": email})
    if user.get("role") != "admin":
        return jsonify({"msg": "Unauthorized"}), 403

    requests = list(leave_requests_col.find())
    for r in requests:
        r["_id"] = str(r["_id"])
    return jsonify(requests), 200

@admin_bp.route("/leave-requests/<req_id>", methods=["PUT"])
@jwt_required()
def update_leave_status(req_id):
    users_col = mongo.db.users
    leave_requests_col = mongo.db.leave_requests

    email = get_jwt_identity()
    user = users_col.find_one({"email": email})
    if user.get("role") != "admin":
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.get_json()
    if "status" not in data:
        return jsonify({"msg": "Missing status field"}), 400

    leave_requests_col.update_one(
        {"_id": ObjectId(req_id)},
        {"$set": {"status": data["status"], "updated_at": datetime.now()}}
    )

    return jsonify({"msg": "Leave status updated"}), 200

@admin_bp.route("/holidays", methods=["GET"])
@jwt_required()
def get_holidays():
    holidays_col = mongo.db.holidays
    holidays = list(holidays_col.find().sort("date", 1))
    for h in holidays:
        h["_id"] = str(h["_id"])
    return jsonify(holidays), 200
    
@admin_bp.route("/holidays", methods=["POST"])
@jwt_required()
def add_holiday():
    holidays_col = mongo.db.holidays
    data = request.get_json()
    date = data.get("date")
    name = data.get("name")

    if not date or not name:
        return jsonify({"msg": "Date and name are required"}), 400

    # Ensure no duplicate for same date
    if holidays_col.find_one({"date": date}):
        return jsonify({"msg": "Holiday for this date already exists"}), 409

    holidays_col.insert_one({
        "date": date,
        "name": name,
        "created_at": datetime.now()
    })

    return jsonify({"msg": "Holiday added successfully"}), 201

@admin_bp.route("/holidays/<holiday_id>", methods=["DELETE"])
@jwt_required()
def delete_holiday(holiday_id):
    holidays_col = mongo.db.holidays
    if not ObjectId.is_valid(holiday_id):
        return jsonify({"msg": "Invalid holiday ID"}), 400

    result = holidays_col.delete_one({"_id": ObjectId(holiday_id)})
    if result.deleted_count == 0:
        return jsonify({"msg": "Holiday not found"}), 404

    return jsonify({"msg": "Holiday deleted successfully"}), 200
    
@admin_bp.route("/leave-balances", methods=["GET"])
@jwt_required()
def list_all_balances():
    users_col = mongo.db.users
    leave_balances = mongo.db.leave_balance

    admin_email = get_jwt_identity()
    admin = users_col.find_one({"email": admin_email})
    if not admin or admin.get("role") != "admin":
        return jsonify({"msg": "Unauthorized"}), 403

    all_balances = list(leave_balances.find())
    for b in all_balances:
        b["_id"] = str(b["_id"])
    return jsonify(all_balances), 200



