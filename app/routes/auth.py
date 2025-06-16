from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta
import re

from app.extensions import mongo
from app.utils.validators import is_valid_email

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    users_col = mongo.db.users  # moved inside function
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "employee")

    if not all([name, email, password]):
        return jsonify({"msg": "All fields are required"}), 400
    if not re.fullmatch(r"[A-Za-z ]+", name):
        return jsonify({"msg": "Name must contain only letters and spaces"}), 400
    if len(password) < 8:
        return jsonify({"msg": "Password must be at least 8 characters"}), 400
    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email format"}), 400
    if users_col.find_one({"email": email}):
        return jsonify({"msg": "Email already registered"}), 409

    hashed_pw = generate_password_hash(password)
    users_col.insert_one({
        "name": name,
        "email": email,
        "password": hashed_pw,
        "role": role
    })
    return jsonify({"msg": "Signup successful"}), 201

@auth_bp.route("/login", methods=["POST","OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    # Respond to CORS preflight request
    data = request.get_json()
    users_col = mongo.db.users  # moved inside function
 
    email = data.get("email", "").strip()
    password = data.get("password", "")

    user = users_col.find_one({"email": email})
    print("🔍 Email received:", email)
    print("📦 Found user in DB:", user)
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"msg": "Invalid credentials"}), 401

    token = create_access_token(
        identity=email,
        additional_claims={"role": user["role"]},
        expires_delta=timedelta(hours=8)
    )
    return jsonify({"token": token, "role": user["role"], "name": user["name"]}), 200

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    users_col = mongo.db.users  # moved inside function
    data = request.get_json()
    email = data.get("email", "").strip()
    new_pw = data.get("new_password", "")

    if not email or not new_pw:
        return jsonify({"msg": "Missing email or new password"}), 400
    if len(new_pw) < 8:
        return jsonify({"msg": "Password must be at least 8 characters"}), 400

    user = users_col.find_one({"email": email})
    if not user:
        return jsonify({"msg": "User not found"}), 404

    hashed_password = generate_password_hash(new_pw)
    users_col.update_one({'email': email}, {'$set': {'password': hashed_password}})

    return jsonify({"msg": "Password reset successful"}), 200