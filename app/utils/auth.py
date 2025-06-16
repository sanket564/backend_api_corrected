from werkzeug.security import generate_password_hash, check_password_hash
import re

def validate_password(password):
    return len(password) >= 8

def validate_name(name):
    return re.fullmatch(r"[A-Za-z ]+", name) is not None

def validate_email(email):
    return re.fullmatch(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None

def hash_password(password):
    return generate_password_hash(password)

def verify_password(stored_hash, password):
    return check_password_hash(stored_hash, password)

from flask_jwt_extended import get_jwt
from functools import wraps
from flask import jsonify

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"msg": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper
