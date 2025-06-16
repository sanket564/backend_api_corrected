import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "16c8733b8d05fa2e4c9649465b8ea78c34ca4ba1f342bc6a84b5d6d553052ed5")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/attendance_db")
