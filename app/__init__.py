# __init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from config import Config
from app.models import db


def seed_database():
    """Seed initial users if database is empty"""
    from app.models.user import User
    
    # Only seed if no users exist
    if User.query.count() > 0:
        return
    
    print("🌱 Database empty, seeding initial users...")
    
    seed_users = [
        {'firstName': 'Super', 'lastName': 'Admin', 'email': 'superadmin@forum.com',
         'password': 'SuperAdmin123!', 'userType': 'superadmin', 'isActive': True},
        {'firstName': 'Admin', 'lastName': 'User', 'email': 'admin@forum.com',
         'password': 'AdminUser123!', 'userType': 'admin', 'isActive': True},
        {'firstName': 'John', 'lastName': 'Doe', 'email': 'john.doe@example.com',
         'password': 'Password123!', 'userType': 'normal_user', 'isActive': True},
        {'firstName': 'Jane', 'lastName': 'Smith', 'email': 'jane.smith@example.com',
         'password': 'Password123!', 'userType': 'normal_user', 'isActive': True},
    ]
    
    for data in seed_users:
        user = User(
            firstName=data['firstName'],
            lastName=data['lastName'],
            email=data['email'],
            userType=data['userType'],
            isActive=data['isActive']
        )
        user.set_password(data['password'])
        db.session.add(user)
    
    db.session.commit()
    print(f"✅ Seeded {len(seed_users)} users")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    JWTManager(app)

    with app.app_context():
        db.create_all()
        
        # Auto-seed in development mode
        if os.getenv('AUTO_SEED', 'true').lower() == 'true':
            seed_database()

    from app.routes.internal_routes import internal_bp
    app.register_blueprint(internal_bp)

    from app.routes.user_routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/api/users')

    return app