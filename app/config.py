import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "16c8733b8d05fa2e4c9649465b8ea78c34ca4ba1f342bc6a84b5d6d553052ed5")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)      # ⬅️ 15 min access
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://virupaksh:Virupaksh%401234@cluster0.goirrab.mongodb.net/attendance_db?retryWrites=true&w=majority&appName=Cluster0")
    # ✅ Outlook SMTP Email Config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587  
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")  # Sender is same as user
