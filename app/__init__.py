# __init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask_jwt_extended import JWTManager
from config import Config
from app.models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()
    # JWTManager(app)
    return app