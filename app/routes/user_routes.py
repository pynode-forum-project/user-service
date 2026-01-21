# user_routes.py
# External routes for the user service (via Gateway, requires JWT)

import random
import string
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from email_validator import validate_email, EmailNotValidError
from app.models import db
from app.models.user import User

user_bp = Blueprint('users', __name__)

# In-memory storage for email verification codes
# TODO: Replace with Redis in production
_email_verification_codes = {}


def is_admin(jwt_claims):
    """Check if user is admin or superadmin based on JWT claims"""
    user_type = jwt_claims.get('userType', '')
    return user_type in ['admin', 'superadmin']


@user_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current logged-in user's profile (used to restore login state)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if not user.isActive:
        return jsonify({'message': 'Your account has been suspended'}), 403
    
    return jsonify(user.to_dict()), 200


@user_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user_profile():
    """Update current user's profile (firstName, lastName)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if not user.isActive:
        return jsonify({'message': 'Your account has been suspended'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Request body is required'}), 400
    
    # Collect validation errors
    errors = {}
    
    # Allowed fields to update
    allowed_fields = ['firstName', 'lastName']
    
    for field in allowed_fields:
        if field in data:
            # Validate field lengths
            if data[field] and len(data[field]) > 50:
                errors[field] = 'Must be at most 50 characters'
            elif not data[field]:
                errors[field] = f'{field} cannot be empty'
    
    if errors:
        return jsonify({
            'message': 'Validation failed',
            'details': errors
        }), 400
    
    # Apply updates
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update profile', 'details': {'server': str(e)}}), 500


@user_bp.route('/me/profile-image', methods=['PUT'])
@jwt_required()
def update_profile_image():
    """Update current user's profile image URL"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if not user.isActive:
        return jsonify({'message': 'Your account has been suspended'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Request body is required'}), 400
    
    profile_image_url = data.get('profileImageURL')
    
    if not profile_image_url:
        return jsonify({
            'message': 'Validation failed',
            'details': {'profileImageURL': 'profileImageURL is required'}
        }), 400
    
    # Validate URL length
    if len(profile_image_url) > 255:
        return jsonify({
            'message': 'Validation failed',
            'details': {'profileImageURL': 'URL must be at most 255 characters'}
        }), 400
    
    user.profileImageURL = profile_image_url
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile image updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update profile image', 'details': {'server': str(e)}}), 500


def _generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))


def _send_verification_email(email, code):
    """
    Send verification email via RabbitMQ (Email Service)
    TODO: Implement RabbitMQ integration or call Auth Service
    For now, we'll log it (in production, integrate with Email Service)
    """
    # TODO: Integrate with RabbitMQ or Auth Service to send email
    # For now, log the code (in development, you can check logs)
    current_app.logger.info(f"Verification code for {email}: {code}")
    # In production, send to RabbitMQ queue for Email Service
    return True


@user_bp.route('/me/email/request-update', methods=['POST'])
@jwt_required()
def request_email_update():
    """Request email update (sends verification code to new email)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if not user.isActive:
        return jsonify({'message': 'Your account has been suspended'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Request body is required'}), 400
    
    new_email = data.get('newEmail')
    
    if not new_email:
        return jsonify({
            'message': 'Validation failed',
            'details': {'newEmail': 'newEmail is required'}
        }), 400
    
    # Validate email format
    try:
        validate_email(new_email, check_deliverability=not current_app.debug)
    except Exception:
        return jsonify({
            'message': 'Validation failed',
            'details': {'newEmail': 'Invalid email format'}
        }), 400
    
    # Check if new email is the same as current email
    if new_email.lower() == user.email.lower():
        return jsonify({
            'message': 'Validation failed',
            'details': {'newEmail': 'New email must be different from current email'}
        }), 400
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=new_email).first()
    if existing_user:
        return jsonify({
            'message': 'Validation failed',
            'details': {'newEmail': 'Email already in use'}
        }), 409
    
    # Generate verification code
    verification_code = _generate_verification_code()
    
    # Store verification code (expires in 10 minutes)
    _email_verification_codes[user_id] = {
        'new_email': new_email,
        'code': verification_code,
        'expires_at': datetime.utcnow() + timedelta(minutes=10)
    }
    
    # Send verification email
    try:
        _send_verification_email(new_email, verification_code)
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {str(e)}")
        return jsonify({
            'message': 'Failed to send verification email',
            'details': {'server': str(e)}
        }), 500
    
    return jsonify({
        'message': 'Verification code sent to new email address'
    }), 200


@user_bp.route('/me/email/confirm-update', methods=['POST'])
@jwt_required()
def confirm_email_update():
    """Confirm email update with verification code"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if not user.isActive:
        return jsonify({'message': 'Your account has been suspended'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Request body is required'}), 400
    
    new_email = data.get('newEmail')
    verification_code = data.get('verificationCode')
    
    if not new_email or not verification_code:
        return jsonify({
            'message': 'Validation failed',
            'details': {
                'newEmail': 'newEmail is required' if not new_email else None,
                'verificationCode': 'verificationCode is required' if not verification_code else None
            }
        }), 400
    
    # Check if verification code exists
    if user_id not in _email_verification_codes:
        return jsonify({
            'message': 'Verification failed',
            'details': {'verificationCode': 'No pending email update request found'}
        }), 400
    
    stored_data = _email_verification_codes[user_id]
    
    # Check if code expired
    if datetime.utcnow() > stored_data['expires_at']:
        del _email_verification_codes[user_id]
        return jsonify({
            'message': 'Verification failed',
            'details': {'verificationCode': 'Verification code has expired'}
        }), 400
    
    # Verify email and code match
    if stored_data['new_email'].lower() != new_email.lower():
        return jsonify({
            'message': 'Verification failed',
            'details': {'newEmail': 'Email does not match the pending request'}
        }), 400
    
    if stored_data['code'] != verification_code:
        return jsonify({
            'message': 'Verification failed',
            'details': {'verificationCode': 'Invalid verification code'}
        }), 400
    
    # Check if email still available (in case another user registered with it)
    existing_user = User.query.filter_by(email=new_email).first()
    if existing_user:
        del _email_verification_codes[user_id]
        return jsonify({
            'message': 'Validation failed',
            'details': {'newEmail': 'Email already in use'}
        }), 409
    
    # Update email and reset userType to 'unverified' (per requirements)
    old_email = user.email
    user.email = new_email
    user.userType = 'unverified'  # Reset to unverified after email change
    
    try:
        db.session.commit()
        # Clean up verification code
        del _email_verification_codes[user_id]
        
        return jsonify({
            'message': 'Email updated successfully. Please verify your new email address.',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'message': 'Failed to update email',
            'details': {'server': str(e)}
        }), 500


@user_bp.route('/<string:user_id>/profile', methods=['GET'])
@jwt_required()
def get_user_profile(user_id):
    """Get a user's profile by ID"""
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Return profile (public info)
    return jsonify(user.to_dict()), 200


@user_bp.route('/<string:user_id>/profile', methods=['PUT'])
@jwt_required()
def update_user_profile(user_id):
    """Update a user's profile (only own profile)"""
    current_user_id = get_jwt_identity()
    
    # Users can only update their own profile
    if current_user_id != user_id:
        return jsonify({'message': 'You can only update your own profile'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Request body is required'}), 400
    
    # Collect validation errors
    errors = {}
    
    # Allowed fields to update
    allowed_fields = ['firstName', 'lastName', 'profileImageURL']
    
    for field in allowed_fields:
        if field in data:
            # Validate field lengths
            if field in ['firstName', 'lastName'] and data[field] and len(data[field]) > 50:
                errors[field] = 'Must be at most 50 characters'
    
    if errors:
        return jsonify({
            'message': 'Validation failed',
            'details': errors
        }), 400
    
    # Apply updates
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update profile', 'details': {'server': str(e)}}), 500


@user_bp.route('', methods=['GET'])
@jwt_required()
def list_users():
    """List all users (Admin only)"""
    jwt_claims = get_jwt()
    
    if not is_admin(jwt_claims):
        return jsonify({'message': 'Admin access required'}), 403
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Limit per_page to prevent abuse
    per_page = min(per_page, 100)
    
    # Query with pagination
    pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)
    
    users = [user.to_dict() for user in pagination.items]
    
    return jsonify({
        'users': users,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@user_bp.route('/<string:user_id>/status', methods=['PUT'])
@jwt_required()
def update_user_status(user_id):
    """Ban or unban a user (Admin only)"""
    jwt_claims = get_jwt()
    
    if not is_admin(jwt_claims):
        return jsonify({'message': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Prevent banning superadmin
    if user.userType == 'superadmin':
        return jsonify({'message': 'Cannot modify superadmin status'}), 403
    
    data = request.get_json()
    
    if not data or 'isActive' not in data:
        return jsonify({
            'message': 'Validation failed',
            'details': {'isActive': 'isActive field is required'}
        }), 400
    
    user.isActive = data['isActive']
    
    try:
        db.session.commit()
        action = 'unbanned' if user.isActive else 'banned'
        return jsonify({
            'message': f'User {action} successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update user status', 'details': {'server': str(e)}}), 500
