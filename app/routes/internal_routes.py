# internal_routes.py
# Internal routes for the user service (called by Auth Service)

from flask import Blueprint, request, jsonify, current_app
from email_validator import validate_email, EmailNotValidError
from app.models import db
from app.models.user import User

internal_bp = Blueprint('internal', __name__, url_prefix='/internal/users')


@internal_bp.route('', methods=['POST'])
def create_user():
    """Create a new user (called by Auth Service during registration)"""
    data = request.get_json()
    
    # Check required fields
    required_fields = ['firstName', 'lastName', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate field lengths (must match frontend validation)
    if len(data['firstName']) > 50:
        return jsonify({'error': 'firstName must be at most 50 characters'}), 400
    if len(data['lastName']) > 50:
        return jsonify({'error': 'lastName must be at most 50 characters'}), 400
    if len(data['password']) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    # Validate email format
    try:
        validate_email(data['email'], check_deliverability= not current_app.debug)
    except EmailNotValidError as e:
        return jsonify({'error': 'Invalid email format', 'details': str(e)}), 400
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create user
    user = User(
        firstName=data['firstName'],
        lastName=data['lastName'],
        email=data['email']
    )
    
    # Hash the password
    user.set_password(data['password'])
    
    # Save to database
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user', 'details': str(e)}), 500
    
    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201


@internal_bp.route('/<string:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a user by ID"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200

@internal_bp.route('/email', methods=['GET'])
def get_user_by_email():
    """Get a user by email"""
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200

@internal_bp.route('/<string:user_id>/verify', methods=['PUT'])
def verify_user(user_id):
    """Verify a user's email"""
    user = User.query.get_or_404(user_id)
    user.userType = 'normal_user'  # 改这个，不是 isActive
    try:
        db.session.commit()
        return jsonify({'message': 'User verified successfully', 'user': user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to verify user', 'details': str(e)}), 500