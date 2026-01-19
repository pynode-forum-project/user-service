# __init__.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from app.models.user import User