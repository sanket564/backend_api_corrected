from flask import Flask
from flask_cors import CORS
from app.extensions import jwt, mongo
from app.config import Config
from app.routes.auth import auth_bp
from app.routes.attendance import attendance_bp
from app.routes.admin import admin_bp
from app.routes.leave import leave_bp
from app.routes.employee import employee_bp
from app.routes.success import success_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)


    # Add this line below app creation
    CORS(app, supports_credentials=True, origins=["http://localhost:3000"], expose_headers=["Authorization"])

    # Initialize extensions
    jwt.init_app(app)
    mongo.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(attendance_bp, url_prefix="/attendance")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(leave_bp, url_prefix="/leave")
    app.register_blueprint(employee_bp, url_prefix="/employee")
    app.register_blueprint(success_bp, url_prefix="/")

    return app