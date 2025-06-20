from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from dateutil import parser
from pytz import timezone, utc

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

# @attendance_bp.route("/checkin", methods=["POST"])
# @jwt_required()
# def checkin():
#     email = get_jwt_identity()
#     data = request.get_json()
#     print("📥 Received data in checkin route:", data)

#     users_col = mongo.db.users
#     logs_col = mongo.db.logs
#     pending_checkins_col = mongo.db.pending_checkins

#     if not data or 'datetime' not in data:
#         return jsonify({"msg": "Missing datetime"}), 400

#     requested_datetime = datetime.strptime(data['datetime'], "%Y-%m-%dT%H:%M")
#     date_str = requested_datetime.strftime('%Y-%m-%d')

#     user = users_col.find_one({"email": email})
#     doj = datetime.strptime(user.get("join_date", ""), "%Y-%m-%d")

#     if requested_datetime < doj:
#         return jsonify({"msg": "You cannot check in before your date of joining."}), 400

#     # Prevent duplicate
#     if logs_col.find_one({"email": email, "date": date_str}):
#         return jsonify({"msg": "Already checked in on this day"}), 400

#     if pending_checkins_col.find_one({"email": email, "date": date_str, "status": "Pending"}):
#         return jsonify({"msg": "Check-in request already submitted and awaiting approval"}), 400

#     # Insert as pending
#     pending_checkins_col.insert_one({
#         "email": email,
#         "date": date_str,
#         "requested_at": requested_datetime,
#         "status": "Pending"
#     })

#     return jsonify({"msg": "Check-in request submitted. Awaiting admin approval."}), 200




# @attendance_bp.route("/checkin", methods=["POST"])
# @jwt_required()
# def checkin():
#     email = get_jwt_identity()
#     data = request.get_json()
#     print("📥 Received data in checkin route:", data)

#     users_col = mongo.db.users
#     logs_col = mongo.db.logs
#     pending_checkins_col = mongo.db.pending_checkins
#     india = timezone("Asia/Kolkata")

#     if not data or 'datetime' not in data:
#         return jsonify({"msg": "Missing datetime"}), 400

#     requested_datetime_ist = india.localize(datetime.strptime(data['datetime'], "%Y-%m-%dT%H:%M"))
#     requested_datetime_utc = requested_datetime_ist.astimezone(utc)
#     date_str = requested_datetime_ist.strftime('%Y-%m-%d')  # date is always in IST

#     user = users_col.find_one({"email": email})
#     doj = india.localize(datetime.strptime(user.get("join_date", ""), "%Y-%m-%d"))
#     # doj = datetime.strptime(user.get("join_date", ""), "%Y-%m-%d")

#     if requested_datetime_ist < doj:
#         return jsonify({"msg": "You cannot check in before your date of joining."}), 400

#     if logs_col.find_one({"email": email, "date": date_str}):
#         return jsonify({"msg": "Already checked in on this day"}), 400

#     if pending_checkins_col.find_one({"email": email, "date": date_str, "status": "Pending"}):
#         return jsonify({"msg": "Check-in request already submitted and awaiting approval"}), 400

#     pending_checkins_col.insert_one({
#         "email": email,
#         "date": date_str,  # still IST date string
#         "requested_at": requested_datetime_utc,
#         "status": "Pending"
#     })

#     return jsonify({"msg": "Check-in request submitted. Awaiting admin approval."}), 200

# @attendance_bp.route("/checkin", methods=["POST"])
# @jwt_required()
# def checkin():
#     email = get_jwt_identity()
#     data = request.get_json()
#     print("📥 Received data in checkin route:", data)

#     users_col = mongo.db.users
#     logs_col = mongo.db.logs
#     pending_checkins_col = mongo.db.pending_checkins


#     if not data or 'datetime' not in data:
#         return jsonify({"msg": "Missing datetime"}), 400

#     # requested_datetime = datetime.strptime(data['datetime'], "%Y-%m-%dT%H:%M")
#     india = timezone("Asia/Kolkata")
#     requested_datetime_ist = india.localize(datetime.strptime(data['datetime'], "%Y-%m-%dT%H:%M"))
#     requested_datetime_utc = requested_datetime_ist.astimezone(utc)
#     date_str = requested_datetime_ist.strftime('%Y-%m-%d')

#     user = users_col.find_one({"email": email})
#     # doj = datetime.strptime(user.get("join_date", ""), "%Y-%m-%d")
#     doj = india.localize(datetime.strptime(user.get("join_date", ""), "%Y-%m-%d"))


#     if  requested_datetime_ist < doj:
#         return jsonify({"msg": "You cannot check in before your date of joining."}), 400

#     # Prevent duplicate
#     if logs_col.find_one({"email": email, "date": date_str}):
#         return jsonify({"msg": "Already checked in on this day"}), 400

#     if pending_checkins_col.find_one({"email": email, "date": date_str, "status": "Pending"}):
#         return jsonify({"msg": "Check-in request already submitted and awaiting approval"}), 400

#     # Insert as pending
#     pending_checkins_col.insert_one({
#         "email": email,
#         "date": date_str,
#         "requested_at": requested_datetime_utc,
#         "status": "Pending"
#     })

#     return jsonify({"msg": "Check-in request submitted. Awaiting admin approval."}), 200


@attendance_bp.route("/checkin", methods=["POST"])
@jwt_required()
def checkin():
    email = get_jwt_identity()
    data = request.get_json()
    print("📥 Received data in checkin route:", data)

    users_col = mongo.db.users
    logs_col = mongo.db.logs
    pending_checkins_col = mongo.db.pending_checkins

    if not data or 'datetime' not in data:
        return jsonify({"msg": "Missing datetime"}), 400

    # Convert to IST and UTC
    india = timezone("Asia/Kolkata")
    try:
        requested_datetime_ist = india.localize(datetime.strptime(data['datetime'], "%Y-%m-%dT%H:%M"))
    except ValueError:
        return jsonify({"msg": "Invalid datetime format"}), 400

    requested_datetime_utc = requested_datetime_ist.astimezone(utc)
    date_str = requested_datetime_ist.strftime('%Y-%m-%d')

    # Get user and DOJ
    user = users_col.find_one({"email": email})
    if not user:
        return jsonify({"msg": "User not found"}), 404

    try:
        doj = india.localize(datetime.strptime(user.get("join_date", ""), "%Y-%m-%d"))
    except:
        return jsonify({"msg": "Invalid or missing date of joining"}), 400

    # 🛑 Cannot check in before DOJ
    if requested_datetime_ist < doj:
        return jsonify({"msg": "You cannot check in before your date of joining."}), 400

    # 🛑 Check for existing check-in for today
    if logs_col.find_one({"email": email, "date": date_str}):
        return jsonify({"msg": "Already checked in on this day"}), 400

    # 🛑 Check for pending approval for today
    if pending_checkins_col.find_one({"email": email, "date": date_str, "status": "Pending"}):
        return jsonify({"msg": "Check-in request already submitted and awaiting approval"}), 400

    # 🛑 Check for previous day incomplete checkout
    previous_log = logs_col.find_one({
        "email": email,
        "checkin": {"$exists": True},
        "checkout": None,
        "date": {"$ne": date_str}
    })
    if previous_log:
        return jsonify({"msg": "You have a pending checkout from a previous day. Please contact admin."}), 400

    # ✅ Insert as pending check-in
    pending_checkins_col.insert_one({
        "email": email,
        "date": date_str,
        "requested_at": requested_datetime_utc,
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

# @attendance_bp.route("/checkout", methods=["POST"])
# @jwt_required()
# def checkout():
#     email = get_jwt_identity()
#     data = request.json or {}
#     print("📥 Checkout data received:", data)

#     users_col = mongo.db.users
#     logs_col = mongo.db.logs

#     if "datetime" not in data:
#         return jsonify({"msg": "Missing datetime"}), 400

#     try:
#         checkout_datetime = datetime.strptime(data["datetime"], "%Y-%m-%dT%H:%M")
#         print("🧪 Parsed checkout datetime:", checkout_datetime)
#     except ValueError:
#         return jsonify({"msg": "Invalid datetime format"}), 400

#     # Get employee's join date
#     user = users_col.find_one({"email": email})
#     if not user:
#         return jsonify({"msg": "User not found"}), 404

#     join_date = datetime.strptime(user["join_date"], "%Y-%m-%d")
#     print("🧪 User join date:", join_date)

#     if checkout_datetime.date() < join_date.date():
#         return jsonify({"msg": "Check-out cannot be before date of joining"}), 400

#     # Find last log with check-in but no check-out
#     log = logs_col.find_one(
#         {"email": email, "checkin": {"$exists": True}, "checkout": None},
#         sort=[("date", -1)]
#     )
#     print("🧪 Checking log:", log)
#     print("🧪 Existing checkin:", log["checkin"] if log else "No log")

#     if not log:
#         return jsonify({"msg": "Please check-in first"}), 400

#     # ✅ Convert check-in string to datetime if needed
#     if isinstance(log["checkin"], str):
#         try:
#             checkin_datetime = parser.parse(f"{log['date']} {log['checkin']}")
#         except Exception:
#             return jsonify({"msg": "Invalid check-in format"}), 400
#     else:
#         checkin_datetime = log["checkin"]

#     if checkout_datetime <= checkin_datetime:
#         return jsonify({"msg": "Check-out must be after check-in"}), 400

#     # Update
#     logs_col.update_one(
#         {"_id": log["_id"]},
#         {"$set": {"checkout": checkout_datetime}}
#     )

#     return jsonify({"msg": "Checked out successfully"}), 200

# @attendance_bp.route("/checkout", methods=["POST"])
# @jwt_required()
# def checkout():
#     email = get_jwt_identity()
#     data = request.json or {}
#     print("📥 Checkout data received:", data)

#     users_col = mongo.db.users
#     logs_col = mongo.db.logs
#     india = timezone("Asia/Kolkata")

#     if "datetime" not in data:
#         return jsonify({"msg": "Missing datetime"}), 400

#     try:
#         checkout_ist = india.localize(datetime.strptime(data["datetime"], "%Y-%m-%dT%H:%M"))
#         checkout_utc = checkout_ist.astimezone(utc)
#         print("🧪 Parsed checkout datetime (IST):", checkout_ist)
#     except ValueError:
#         return jsonify({"msg": "Invalid datetime format"}), 400

#     user = users_col.find_one({"email": email})
#     if not user:
#         return jsonify({"msg": "User not found"}), 404

#     join_date = datetime.strptime(user["join_date"], "%Y-%m-%d")

#     if checkout_ist.date() < join_date.date():
#         return jsonify({"msg": "Check-out cannot be before date of joining"}), 400

#     log = logs_col.find_one(
#         {"email": email, "checkin": {"$exists": True}, "checkout": None},
#         sort=[("date", -1)]
#     )

#     if not log:
#         return jsonify({"msg": "Please check-in first"}), 400

#     # Convert check-in to datetime if needed
#     if isinstance(log["checkin"], str):
#         try:
#             checkin_ist = india.localize(datetime.strptime(f"{log['date']} {log['checkin']}", "%Y-%m-%d %H:%M"))
#             checkin_utc = checkin_ist.astimezone(utc)
#         except Exception:
#             return jsonify({"msg": "Invalid check-in format"}), 400
#     else:
#         checkin_utc = log["checkin"]

#     if checkout_utc <= checkin_utc:
#         return jsonify({"msg": "Check-out must be after check-in"}), 400

#     logs_col.update_one(
#         {"_id": log["_id"]},
#         {"$set": {"checkout": checkout_utc}}
#     )

#     return jsonify({"msg": "Checked out successfully"}), 200
# @attendance_bp.route("/checkout", methods=["POST"])
# @jwt_required()
# def checkout():
#     email = get_jwt_identity()
#     data = request.json or {}
#     print("📥 Checkout data received:", data)

#     users_col = mongo.db.users
#     logs_col = mongo.db.logs
#     india = timezone("Asia/Kolkata")

#     if "datetime" not in data:
#         return jsonify({"msg": "Missing datetime"}), 400

#     try:
#         checkout_ist = india.localize(datetime.strptime(data["datetime"], "%Y-%m-%dT%H:%M"))
#         checkout_utc = checkout_ist.astimezone(utc)
#         print("🧪 Parsed checkout datetime (IST):", checkout_ist)
#     except ValueError:
#         return jsonify({"msg": "Invalid datetime format"}), 400

#     user = users_col.find_one({"email": email})
#     if not user:
#         return jsonify({"msg": "User not found"}), 404

#     join_date = datetime.strptime(user["join_date"], "%Y-%m-%d")
#     if checkout_ist.date() < join_date.date():
#         return jsonify({"msg": "Check-out cannot be before date of joining"}), 400

#     log = logs_col.find_one(
#         {"email": email, "checkin": {"$exists": True}, "checkout": None},
#         sort=[("date", -1)]
#     )

#     if not log:
#         return jsonify({"msg": "Please check-in first"}), 400

#     # Handle check-in comparison safely
#     if isinstance(log["checkin"], str):
#         try:
#             checkin_ist = india.localize(datetime.strptime(f"{log['date']} {log['checkin']}", "%Y-%m-%d %H:%M"))
#             checkin_utc = checkin_ist.astimezone(utc)
#         except Exception:
#             return jsonify({"msg": "Invalid check-in format"}), 400
#     else:
#         checkin_utc = log["checkin"]
#         if checkin_utc.tzinfo is None:
#             checkin_utc = utc.localize(checkin_utc)

#     if checkout_utc <= checkin_utc:
#         return jsonify({"msg": "Check-out must be after check-in"}), 400

#     logs_col.update_one(
#         {"_id": log["_id"]},
#         {"$set": {"checkout": checkout_utc}}
#     )

#     return jsonify({"msg": "Checked out successfully"}), 200

# @attendance_bp.route("/checkout", methods=["POST"])
# @jwt_required()
# def checkout():
#     email = get_jwt_identity()
#     data = request.json or {}
#     print("📥 Checkout data received:", data)

#     users_col = mongo.db.users
#     logs_col = mongo.db.logs

#     if "datetime" not in data:
#         return jsonify({"msg": "Missing datetime"}), 400

#     try:
#         checkout_datetime = datetime.strptime(data["datetime"], "%Y-%m-%dT%H:%M")
#         print("🧪 Parsed checkout datetime:", checkout_datetime)
#     except ValueError:
#         return jsonify({"msg": "Invalid datetime format"}), 400

#     # Get employee's join date
#     user = users_col.find_one({"email": email})
#     if not user:
#         return jsonify({"msg": "User not found"}), 404

#     join_date = datetime.strptime(user["join_date"], "%Y-%m-%d")
#     print("🧪 User join date:", join_date)

#     if checkout_datetime.date() < join_date.date():
#         return jsonify({"msg": "Check-out cannot be before date of joining"}), 400

#     # Find last log with check-in but no check-out
#     log = logs_col.find_one(
#         {"email": email, "checkin": {"$exists": True}, "checkout": None},
#         sort=[("date", -1)]
#     )
#     print("🧪 Checking log:", log)
#     print("🧪 Existing checkin:", log["checkin"] if log else "No log")

#     if not log:
#         return jsonify({"msg": "Please check-in first"}), 400

#     # ✅ Convert check-in string to datetime if needed
#     if isinstance(log["checkin"], str):
#         try:
#             checkin_datetime = parser.parse(f"{log['date']} {log['checkin']}")
#         except Exception:
#             return jsonify({"msg": "Invalid check-in format"}), 400
#     else:
#         checkin_datetime = log["checkin"]

   
#     if checkin_datetime.tzinfo is None:
#         checkin_datetime = utc.localize(checkin_datetime)
#     if checkout_datetime.tzinfo is None:
#         checkout_datetime = utc.localize(checkout_datetime)


#     if checkout_datetime <= checkin_datetime:
#         return jsonify({"msg": "Check-out must be after check-in"}), 400

#     # Update
#     logs_col.update_one(
#         {"_id": log["_id"]},
#         {"$set": {"checkout": checkout_datetime}}
#     )

#     return jsonify({"msg": "Checked out successfully"}), 200

# @attendance_bp.route("/checkout", methods=["POST"])
# @jwt_required()
# def checkout():
#     email = get_jwt_identity()
#     data = request.json or {}
#     print("📥 Checkout data received:", data)

#     users_col = mongo.db.users
#     logs_col = mongo.db.logs

#     if "datetime" not in data:
#         return jsonify({"msg": "Missing datetime"}), 400

#     try:
#         india = timezone("Asia/Kolkata")
#         checkout_datetime_ist = india.localize(datetime.strptime(data["datetime"], "%Y-%m-%dT%H:%M"))
#         checkout_datetime = checkout_datetime_ist.astimezone(utc)
#         print("🕐 Converted checkout to UTC:", checkout_datetime)
#     except ValueError:
#         return jsonify({"msg": "Invalid datetime format"}), 400

#     user = users_col.find_one({"email": email})
#     if not user:
#         return jsonify({"msg": "User not found"}), 404

#     join_date = datetime.strptime(user["join_date"], "%Y-%m-%d")
#     if checkout_datetime_ist.date() < join_date.date():
#         return jsonify({"msg": "Check-out cannot be before date of joining"}), 400

#     log = logs_col.find_one(
#         {"email": email, "checkin": {"$exists": True}, "checkout": None},
#         sort=[("date", -1)]
#     )

#     if not log:
#         return jsonify({"msg": "Please check-in first"}), 400

#     # ✅ Normalize check-in time to UTC if needed
#     if isinstance(log["checkin"], str):
#         try:
#             checkin_datetime = parser.parse(f"{log['date']} {log['checkin']}")
#         except Exception:
#             return jsonify({"msg": "Invalid check-in format"}), 400
#     else:
#         checkin_datetime = log["checkin"]

#     if checkin_datetime.tzinfo is None:
#         checkin_datetime = utc.localize(checkin_datetime)

#     if checkout_datetime <= checkin_datetime:
#         return jsonify({"msg": "Check-out must be after check-in"}), 400

#     logs_col.update_one(
#         {"_id": log["_id"]},
#         {"$set": {"checkout": checkout_datetime}}
#     )

#     return jsonify({"msg": "Checked out successfully"}), 200
@attendance_bp.route("/checkout", methods=["POST"])
@jwt_required()
def checkout():
    email = get_jwt_identity()
    data = request.json or {}
    print("📥 Checkout data received:", data)

    users_col = mongo.db.users
    logs_col = mongo.db.logs

    if "datetime" not in data:
        return jsonify({"msg": "Missing datetime"}), 400

    try:
        india = timezone("Asia/Kolkata")
        checkout_datetime_ist = india.localize(datetime.strptime(data["datetime"], "%Y-%m-%dT%H:%M"))
        checkout_datetime = checkout_datetime_ist.astimezone(utc)
        print("🕐 Converted checkout to UTC:", checkout_datetime)
    except ValueError:
        return jsonify({"msg": "Invalid datetime format"}), 400

    user = users_col.find_one({"email": email})
    if not user:
        return jsonify({"msg": "User not found"}), 404

    join_date = datetime.strptime(user["join_date"], "%Y-%m-%d")
    if checkout_datetime_ist.date() < join_date.date():
        return jsonify({"msg": "Check-out cannot be before date of joining"}), 400

    log = logs_col.find_one(
        {"email": email, "checkin": {"$exists": True}, "checkout": None},
        sort=[("date", -1)]
    )

    if not log:
        return jsonify({"msg": "Please check-in first"}), 400

    # ✅ Use check-in as stored in DB (should already be UTC datetime)
    checkin_datetime = log["checkin"]

    if checkin_datetime.tzinfo is None:
        checkin_datetime = utc.localize(checkin_datetime)

    if checkout_datetime <= checkin_datetime:
        return jsonify({"msg": "Check-out must be after check-in"}), 400

    logs_col.update_one(
        {"_id": log["_id"]},
        {"$set": {"checkout": checkout_datetime}}
    )

    return jsonify({"msg": "Checked out successfully"}), 200





# @attendance_bp.route("/history", methods=["GET"])
# @jwt_required()
# def attendance_history():
#     logs_col = mongo.db.logs

#     email = get_jwt_identity()
#     logs = list(logs_col.find({"email": email}).sort("date", -1))
#     for log in logs:
#         log["_id"] = str(log["_id"])
#         for k in ("checkin", "checkout"):
#             if isinstance(log.get(k), datetime):
#                 log[k] = log[k].strftime("%Y-%m-%dT%H:%M:%S")
#     return jsonify(logs), 200



# @attendance_bp.route("/history", methods=["GET"])
# @jwt_required()
# def attendance_history():
#     logs_col = mongo.db.logs
#     email = get_jwt_identity()
#     india = timezone("Asia/Kolkata")

#     logs = list(logs_col.find({"email": email}).sort("date", -1))

#     for log in logs:
#         log["_id"] = str(log["_id"])

#         for k in ("checkin", "checkout"):
#             val = log.get(k)
#             if isinstance(val, datetime):
#                 # Convert from UTC to IST
#                 ist_time = val.astimezone(india)
#                 log[k] = ist_time.strftime("%Y-%m-%dT%H:%M:%S")
#             elif isinstance(val, str):
#                 # Leave string values as-is (legacy fallback)
#                 log[k] = val

#     return jsonify(logs), 200

# @attendance_bp.route("/history", methods=["GET"])
# @jwt_required()
# def attendance_history():
#     logs_col = mongo.db.logs
#     email = get_jwt_identity()
#     india = timezone("Asia/Kolkata")

#     logs = list(logs_col.find({"email": email}).sort("date", -1))

#     for log in logs:
#         log["_id"] = str(log["_id"])

#         for k in ("checkin", "checkout"):
#             val = log.get(k)
#             if isinstance(val, datetime):
#                 # ✅ Ensure datetime is timezone-aware
#                 if val.tzinfo is None:
#                     val = utc.localize(val)  # assume stored as UTC
#                 ist_time = val.astimezone(india)
#                 log[k] = ist_time.strftime("%Y-%m-%d %I:%M %p")  # optional: show AM/PM format
#             elif isinstance(val, str):
#                 log[k] = val  # legacy fallback

#     return jsonify(logs), 200

# @attendance_bp.route('/history', methods=['GET'])
# @jwt_required()
# def attendance_history():
#     email = get_jwt_identity()
    
#     # ✅ Fix: define the collection
#     logs_col = mongo.db.logs

#     logs = list(logs_col.find({"email": email}).sort("date", -1))
    
#     for log in logs:
#         log["_id"] = str(log["_id"])  # Convert ObjectId to string
        
#         # Convert datetime to string
#         if isinstance(log.get("checkin"), datetime):
#             log["checkin"] = log["checkin"].strftime("%Y-%m-%dT%H:%M:%S")
#         if isinstance(log.get("checkout"), datetime):
#             log["checkout"] = log["checkout"].strftime("%Y-%m-%dT%H:%M:%S")
    
#     return jsonify(logs), 200


# @attendance_bp.route('/history', methods=['GET'])
# @jwt_required()
# def attendance_history():
#     logs_col = mongo.db.logs
#     email = get_jwt_identity()
#     india = timezone("Asia/Kolkata")

#     logs = list(logs_col.find({"email": email}).sort("date", -1))

#     for log in logs:
#         log["_id"] = str(log["_id"])

#         for k in ("checkin", "checkout"):
#             val = log.get(k)
#             if isinstance(val, datetime):
#                 # ✅ Assume datetime is in UTC and convert to IST
#                 val = val.replace(tzinfo=timezone("UTC")).astimezone(india)
#                 log[k] = val.strftime("%d-%m-%Y %I:%M %p")  # e.g., "18-06-2025 07:35 PM"

#     return jsonify(logs), 200
@attendance_bp.route('/history', methods=['GET'])
@jwt_required()
def attendance_history():
    logs_col = mongo.db.logs
    email = get_jwt_identity()
    india = timezone("Asia/Kolkata")

    logs = list(logs_col.find({"email": email}).sort("date", -1))

    for log in logs:
        log["_id"] = str(log["_id"])

        for k in ("checkin", "checkout"):
            val = log.get(k)
            if isinstance(val, datetime):
                # ✅ Safely handle both naive and aware datetimes
                if val.tzinfo is None:
                    val = utc.localize(val)  # treat as UTC
                val_ist = val.astimezone(india)
                log[k] = val_ist.strftime("%d-%m-%Y %I:%M %p")

    return jsonify(logs), 200




