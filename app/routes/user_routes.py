from flask import request, jsonify
from app.routes import user_bp
from app.services.user_service import UserService
from app.utils.decorators import handle_exceptions, require_auth, require_admin, require_super_admin

user_service = UserService()


@user_bp.route('', methods=['GET'])
@handle_exceptions
@require_auth
@require_admin
def get_all_users():
    """Get all users (Admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    users, total = user_service.get_all_users(page, per_page)
    
    return jsonify({
        'users': [u.to_public_dict() for u in users],
        'total': total,
        'page': page,
        'perPage': per_page,
        'totalPages': (total + per_page - 1) // per_page
    }), 200


@user_bp.route('/<int:user_id>', methods=['GET'])
@handle_exceptions
@require_auth
def get_user(user_id):
    """Get user by ID"""
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_public_dict()}), 200


@user_bp.route('/<int:user_id>', methods=['PUT'])
@handle_exceptions
@require_auth
def update_user(user_id):
    """Update user profile"""
    current_user_id = request.headers.get('X-User-Id')
    current_user_type = request.headers.get('X-User-Type')
    
    # Users can only update their own profile (unless admin)
    if str(current_user_id) != str(user_id) and current_user_type not in ['admin', 'super_admin']:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    # Validate allowed fields
    allowed_fields = ['firstName', 'lastName', 'email']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not update_data:
        return jsonify({'error': 'No valid fields to update'}), 400
    
    try:
        user, email_changed = user_service.update_user(user_id, update_data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    response_data = {
        'message': 'User updated successfully',
        'user': user.to_public_dict(),
        'emailChanged': email_changed
    }
    
    return jsonify(response_data), 200


@user_bp.route('/<int:user_id>/profile-image', methods=['PUT'])
@handle_exceptions
@require_auth
def update_profile_image(user_id):
    """Update user profile image"""
    current_user_id = request.headers.get('X-User-Id')
    
    if str(current_user_id) != str(user_id):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    image_url = data.get('profileImageUrl')
    
    if not image_url:
        return jsonify({'error': 'Profile image URL is required'}), 400
    
    user = user_service.update_profile_image(user_id, image_url)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'message': 'Profile image updated successfully',
        'user': user.to_public_dict()
    }), 200


@user_bp.route('/<int:user_id>/ban', methods=['PUT'])
@handle_exceptions
@require_auth
@require_admin
def ban_user(user_id):
    """Ban a user (Admin only)"""
    current_user_type = request.headers.get('X-User-Type')
    
    # Get the target user
    target_user = user_service.get_user_by_id(user_id)
    if not target_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Admins cannot ban other admins
    if target_user.type in ['admin', 'super_admin']:
        return jsonify({'error': 'Cannot ban admin users'}), 403
    
    user = user_service.ban_user(user_id)
    
    return jsonify({
        'message': 'User banned successfully',
        'user': user.to_public_dict()
    }), 200


@user_bp.route('/<int:user_id>/unban', methods=['PUT'])
@handle_exceptions
@require_auth
@require_admin
def unban_user(user_id):
    """Unban a user (Admin only)"""
    user = user_service.unban_user(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'message': 'User unbanned successfully',
        'user': user.to_public_dict()
    }), 200


@user_bp.route('/<int:user_id>/promote', methods=['PUT'])
@handle_exceptions
@require_auth
@require_super_admin
def promote_user(user_id):
    """Promote user to admin (Super Admin only)"""
    target_user = user_service.get_user_by_id(user_id)
    
    if not target_user:
        return jsonify({'error': 'User not found'}), 404
    
    if target_user.type in ['admin', 'super_admin']:
        return jsonify({'error': 'User is already an admin'}), 400
    
    user = user_service.promote_to_admin(user_id)
    
    return jsonify({
        'message': 'User promoted to admin successfully',
        'user': user.to_public_dict()
    }), 200


@user_bp.route('/<int:user_id>/demote', methods=['PUT'])
@handle_exceptions
@require_auth
@require_super_admin
def demote_user(user_id):
    """Demote admin to normal user (Super Admin only)"""
    target_user = user_service.get_user_by_id(user_id)
    
    if not target_user:
        return jsonify({'error': 'User not found'}), 404
    
    if target_user.type == 'super_admin':
        return jsonify({'error': 'Cannot demote super admin'}), 403
    
    if target_user.type != 'admin':
        return jsonify({'error': 'User is not an admin'}), 400
    
    user = user_service.demote_from_admin(user_id)
    
    return jsonify({
        'message': 'User demoted to normal user successfully',
        'user': user.to_public_dict()
    }), 200


@user_bp.route('/<int:user_id>', methods=['DELETE'])
@handle_exceptions
@require_auth
@require_super_admin
def delete_user(user_id):
    """Delete a user (Super Admin only)"""
    target_user = user_service.get_user_by_id(user_id)
    
    if not target_user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        success = user_service.delete_user(user_id)
        if not success:
            return jsonify({'error': 'Failed to delete user'}), 500
        
        return jsonify({
            'message': 'User deleted successfully'
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 403
