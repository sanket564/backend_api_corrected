from .auth import auth_bp
from .attendance import attendance_bp
from .admin import admin_bp
from .employee import employee_bp

# List of all blueprints for easy registration
all_blueprints = [
    auth_bp,
    attendance_bp,
    admin_bp,
    employee_bp
]

_all_ = ['auth_bp', 'attendance_bp', 'admin_bp', 'employee_bp']
