# __init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from config import Config
from app.models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    JWTManager(app)

    with app.app_context():
        db.create_all()

    from app.routes.internal_routes import internal_bp
    app.register_blueprint(internal_bp)

    from app.routes.user_routes import user_bp
    app.register_blueprint(user_bp)

    return app