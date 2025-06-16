from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
import csv, io, os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import mongo

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/check", methods=["GET"])
def check_admin_exists():
    users_col = mongo.db.users
    exists = users_col.find_one({"role": "admin"}) is not None
    return jsonify({"exists": exists})

@admin_bp.route("/checkins/pending", methods=["GET"])
@jwt_required()
def get_pending_checkins():
    users_col = mongo.db.users
    pending_checkins_col = mongo.db.pending_checkins

    email = get_jwt_identity()
    if not users_col.find_one({"email": email, "role": "admin"}):
        return jsonify({"msg": "Unauthorized"}), 403

    pending = list(pending_checkins_col.find({"status": "Pending"}))
    for p in pending:
        p["_id"] = str(p["_id"])
        if p.get("requested_at"):
            p["checkin_time"] = p["requested_at"].strftime("%I:%M %p")
    return jsonify(pending), 200

@admin_bp.route("/checkins/approve/<checkin_id>", methods=["POST"])
@jwt_required()
def approve_checkin(checkin_id):
    users_col = mongo.db.users
    logs_col = mongo.db.logs
    pending_checkins_col = mongo.db.pending_checkins

    email = get_jwt_identity()
    if not users_col.find_one({"email": email, "role": "admin"}):
        return jsonify({"msg": "Unauthorized"}), 403

    checkin = pending_checkins_col.find_one({"_id": ObjectId(checkin_id)})
    if not checkin:
        return jsonify({"msg": "Check-in request not found"}), 404

    if logs_col.find_one({"email": checkin["email"], "date": checkin["date"]}):
        return jsonify({"msg": "Check-in already exists"}), 400

    logs_col.insert_one({
        "email": checkin["email"],
        "date": checkin["date"],
        "checkin": checkin["requested_at"].strftime("%H:%M"),
        "checkout": None,
        "approved": True
    })

    pending_checkins_col.update_one({"_id": checkin["_id"]}, {"$set": {"status": "Approved"}})
    return jsonify({"msg": "Check-in approved"}), 200

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
    for r in records:
        r["_id"] = str(r["_id"])
        for k in ("checkin", "checkout"):
            if isinstance(r.get(k), datetime):
                r[k] = r[k].strftime("%I:%M %p")
    return jsonify(records), 200

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
    writer.writerow(["Email", "Date", "Check-In", "Check-Out"])

    for r in records:
        writer.writerow([
            r.get("email"),
            r.get("date"),
            r.get("checkin") if isinstance(r.get("checkin"), str)
            else r["checkin"].strftime("%I:%M %p") if r.get("checkin") else "",
            r.get("checkout") if isinstance(r.get("checkout"), str)
            else r["checkout"].strftime("%I:%M %p") if r.get("checkout") else ""
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
    file.save(filepath)  # 💾 Save the file temporarily

    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            entries = []
            for row in reader:
                # Parse each CSV row and prepare MongoDB entries
                entry = {
                    "email": row["email"].strip(),
                    "date": row["date"].strip(),  # keep as string YYYY-MM-DD
                    "checkin": datetime.strptime(row["checkin"], "%I:%M %p") if row["checkin"] else None,
                    "checkout": datetime.strptime(row["checkout"], "%I:%M %p") if row["checkout"] else None
                }
                entries.append(entry)

            if entries:
                logs_col.insert_many(entries)  # 🗃️ Insert into your MongoDB collection

    except Exception as e:
        print("Error processing CSV:", e)
        return jsonify({"msg": "Failed to process file"}), 500
    finally:
        os.remove(filepath)  # 🧹 Clean up: remove uploaded file after processing

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

@admin_bp.route("/add-employee", methods=["POST"])
@jwt_required()
def add_employee():
    users_col = mongo.db.users
    data = request.get_json()
    required = ("name", "email", "password", "doj")
    
    if not all(k in data for k in required):
        return jsonify({"msg": "Missing required fields"}), 400

    if users_col.find_one({"email": data["email"]}):
        return jsonify({"msg": "Employee already exists"}), 409
    
    hashed_password = generate_password_hash(data["password"])

    users_col.insert_one({
        "name": data["name"],
        "email": data["email"],
        "password": hashed_password,
        "role": "employee",
        "join_date": data["doj"],
        "department": data.get("department", "Not Assigned"),
        "position": data.get("position", "Not Assigned"),
        "blood_group": data.get("blood_group", "Not Provided")  # Added field
    })
    
    return jsonify({"msg": "Employee added successfully"}), 201



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