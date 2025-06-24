from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
import csv, io, os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from pytz import timezone
import dateutil.parser



from app.extensions import mongo

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/check", methods=["GET"])
def check_admin_exists():
    users_col = mongo.db.users
    exists = users_col.find_one({"role": "admin"}) is not None
    return jsonify({"exists": exists})

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


@admin_bp.route("/employees/<emp_id>", methods=["PUT"])
@jwt_required()
def edit_employee(emp_id):
    users_col = mongo.db.users

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

    if not update_fields:
        return jsonify({"msg": "No valid fields to update"}), 400

    users_col.update_one({"_id": ObjectId(emp_id)}, {"$set": update_fields})
    return jsonify({"msg": "Employee updated successfully"}), 200

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

@admin_bp.route("/total-employees", methods=["GET"])
@jwt_required()
def total_employees():
    users_col = mongo.db.users
    count = users_col.count_documents({})
    return jsonify({"total_employees": count}), 200

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


@admin_bp.route("/add-employee", methods=["POST"])
@jwt_required()
def add_employee():
    users_col = mongo.db.users
    data = request.get_json()

    reporting_to = data.get("reporting_to", [])  # List of emails
    proxy_approver = data.get("proxy_approver", None)
    role = data.get("role", "employee")  # 🔄 default to employee if not provided

    # --- 1. Validate required fields ----------------------------------------
    required = ("name", "email", "password", "join_date", "emp_code")
    if not all(k in data for k in required):
        return jsonify({"msg": "Missing required fields"}), 400

    # --- 2. Uniqueness checks ----------------------------------------------
    if users_col.find_one({"email": data["email"]}):
        return jsonify({"msg": "Email already exists"}), 409

    if users_col.find_one({"emp_code": data["emp_code"]}):
        return jsonify({"msg": "Employee code already exists"}), 409

    # --- 3. Insert employee -------------------------------------------------
    hashed_password = generate_password_hash(data["password"])

    users_col.insert_one({
        "name": data["name"],
        "email": data["email"],
        "password": hashed_password,
        "role": role,  # ✅ Use role from frontend
        "join_date": data["join_date"],
        "emp_code": data["emp_code"],
        "department": data.get("department", "Not Assigned"),
        "position": data.get("position", "Not Assigned"),
        "bloodGroup": data.get("bloodGroup", "Not Provided"),
        "reporting_to": reporting_to,
        "proxy_approver": proxy_approver
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



