# user.py
# define the user model

from app.models import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

class User(db.Model):
    __tablename__ = 'users'

    userId = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    firstName = db.Column(db.String(50), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    isActive = db.Column(db.Boolean, default=True)  # True=active, False=banned
    password = db.Column(db.String(255), nullable=False)
    dateJoined = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    userType = db.Column(db.String(50), nullable=False, default='unverified')  # unverified until email verified
    profileImageURL = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self):
        return {
            'userId': self.userId,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email,
            'isActive': self.isActive,
            'dateJoined': self.dateJoined.isoformat() if self.dateJoined else None,
            'userType': self.userType,
            'profileImageURL': self.profileImageURL
        }