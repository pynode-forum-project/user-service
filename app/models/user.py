from datetime import datetime
from app import db


class User(db.Model):
    """User model"""
    
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(255), nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(
        db.Enum('visitor', 'unverified', 'normal', 'admin', 'super_admin'),
        default='unverified'
    )
    profile_image_url = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self, include_password=False):
        """Convert user to dictionary"""
        data = {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'active': self.active,
            'email_verified': self.email_verified,
            'date_joined': self.date_joined.isoformat() if self.date_joined else None,
            'type': self.type,
            'profile_image_url': self.profile_image_url
        }
        
        if include_password:
            data['password'] = self.password
        
        return data
    
    def to_public_dict(self):
        """Convert user to public dictionary (safe to expose)"""
        return {
            'userId': self.user_id,
            'firstName': self.first_name,
            'lastName': self.last_name,
            'email': self.email,
            'active': self.active,
            'emailVerified': self.email_verified,
            'dateJoined': self.date_joined.isoformat() if self.date_joined else None,
            'type': self.type,
            'profileImageUrl': self.profile_image_url
        }
