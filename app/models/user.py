from app.extensions import mongo
from werkzeug.security import generate_password_hash, check_password_hash

def get_user_collection():
    return mongo.db.users

def get_user_by_email(email):
    return get_user_collection().find_one({"email": email})

def create_user(name, email, password, role="employee"):
    hashed_pw = generate_password_hash(password)
    return get_user_collection().insert_one({
        "name": name,
        "email": email,
        "password": hashed_pw,
        "role": role
    })

def verify_password(stored_hash, password):
    return check_password_hash(stored_hash, password)

def update_password(email, new_password):
    return get_user_collection().update_one(
        {"email": email},
        {"$set": {"password": generate_password_hash(new_password)}}
    )
