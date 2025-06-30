from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from flask_mail import Mail

jwt = JWTManager()
mongo = PyMongo()
mail = Mail()
