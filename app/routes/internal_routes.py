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
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    # Collect all validation errors
    errors = {}
    
    # Check required fields
    required_fields = ['firstName', 'lastName', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            errors[field] = f'{field} is required'
    
    # Validate field lengths (only if field exists)
    if data.get('firstName') and len(data['firstName']) > 50:
        errors['firstName'] = 'Must be at most 50 characters'
    if data.get('lastName') and len(data['lastName']) > 50:
        errors['lastName'] = 'Must be at most 50 characters'
    if data.get('password') and len(data['password']) < 8:
        errors['password'] = 'Must be at least 8 characters'
    
    # Validate email format
    if data.get('email'):
        try:
            validate_email(data['email'], check_deliverability=not current_app.debug)
        except EmailNotValidError:
            errors['email'] = 'Invalid email format'
    
    # Return all validation errors at once
    if errors:
        return jsonify({
            'error': 'Validation failed',
            'details': errors
        }), 400
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'User with this email already exists'}), 409
    
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
    
    # Return user info (without password)
    return jsonify({
        'userId': user.userId,
        'firstName': user.firstName,
        'lastName': user.lastName,
        'email': user.email
    }), 201


@internal_bp.route('/<string:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a user by ID"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200


@internal_bp.route('/email', methods=['GET'])
def get_user_by_email():
    """Get a user by email"""
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email query parameter is required'}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200


@internal_bp.route('/<string:user_id>/verify', methods=['PUT'])
def verify_user(user_id):
    """Verify a user's email (change userType to normal_user)"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.userType = 'normal_user'
    try:
        db.session.commit()
        return jsonify({'message': 'User verified successfully', 'user': user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to verify user', 'details': str(e)}), 500


@internal_bp.route('/verify', methods=['POST'])
def verify_credentials():
    """Verify user credentials (called by Auth Service during login)"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    # Validate required fields
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Find user by email
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Verify password
    if not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Return user info for Auth Service to generate JWT
    return jsonify({
        'userId': user.userId,
        'userType': user.userType,
        'isActive': user.isActive
    }), 200
