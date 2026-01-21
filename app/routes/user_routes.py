# user_routes.py
# External routes for the user service (via Gateway, requires JWT)

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import db
from app.models.user import User

user_bp = Blueprint('users', __name__)


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
    
    return jsonify(user.to_dict()), 200


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
