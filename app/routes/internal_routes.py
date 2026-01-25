from flask import request, jsonify
from datetime import datetime
from app.routes import internal_bp
from app.services.user_service import UserService
from app.utils.decorators import handle_exceptions

user_service = UserService()


@internal_bp.route('/users', methods=['POST'])
@handle_exceptions
def create_user():
    """Create a new user (Internal API for Auth Service)"""
    data = request.get_json()
    
    user = user_service.create_user(
        first_name=data.get('firstName'),
        last_name=data.get('lastName'),
        email=data.get('email'),
        password=data.get('password'),
        verification_token=data.get('verificationToken'),
        token_expires_at=data.get('tokenExpiresAt')
    )
    
    return jsonify(user.to_dict(include_password=False)), 201


@internal_bp.route('/users/<int:user_id>', methods=['GET'])
@handle_exceptions
def get_user_internal(user_id):
    """Get user by ID (Internal API)"""
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict(include_password=True)), 200


@internal_bp.route('/users/email/<email>', methods=['GET'])
@handle_exceptions
def get_user_by_email(email):
    """Get user by email (Internal API for Auth Service)"""
    user = user_service.get_user_by_email(email)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict(include_password=True)), 200


@internal_bp.route('/users/verify-email', methods=['POST'])
@handle_exceptions
def verify_email():
    """Verify user email with token (Internal API)"""
    data = request.get_json()
    email = data.get('email')
    token = data.get('token')
    
    user = user_service.get_user_by_email(email)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    if user.email_verified:
        return jsonify({'success': True, 'message': 'Email already verified', 'user': user.to_public_dict()}), 200
    
    if user.verification_token != token:
        return jsonify({'success': False, 'message': 'Invalid verification token'}), 400
    
    if user.token_expires_at and user.token_expires_at < datetime.utcnow():
        return jsonify({'success': False, 'message': 'Verification token has expired'}), 400
    
    # Verify the email
    updated_user = user_service.verify_email(user.user_id)
    
    return jsonify({
        'success': True,
        'message': 'Email verified successfully',
        'user': updated_user.to_public_dict()
    }), 200


@internal_bp.route('/users/<int:user_id>/verification-token', methods=['PUT'])
@handle_exceptions
def update_verification_token(user_id):
    """Update user's verification token (Internal API)"""
    data = request.get_json()
    token = data.get('token')
    expires_at = data.get('expiresAt')
    
    user = user_service.update_verification_token(user_id, token, expires_at)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'message': 'Verification token updated'}), 200


@internal_bp.route('/users/<int:user_id>/verification-token/valid', methods=['GET'])
@handle_exceptions
def get_valid_verification_token(user_id):
    """Get valid verification token if exists and not expired (Internal API)"""
    token, expires_at = user_service.get_valid_verification_token(user_id)
    
    if token:
        return jsonify({
            'token': token,
            'expiresAt': expires_at.isoformat() if expires_at else None
        }), 200
    else:
        return jsonify({'token': None, 'expiresAt': None}), 200
