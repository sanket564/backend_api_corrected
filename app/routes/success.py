from flask import Blueprint

success_bp = Blueprint("/", __name__) 

@success_bp.route("/",methods=['GET'])
def index():
    return "Hello from index!"