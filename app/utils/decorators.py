from functools import wraps
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)


def handle_exceptions(f):
    """Decorator to handle exceptions in route handlers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f'Validation error in {f.__name__}: {str(e)}')
            return jsonify({'error': 'Validation error', 'message': str(e)}), 400
        except PermissionError as e:
            logger.warning(f'Permission denied in {f.__name__}: {str(e)}')
            return jsonify({'error': 'Access denied', 'message': str(e)}), 403
        except Exception as e:
            logger.error(f'Error in {f.__name__}: {str(e)}', exc_info=True)
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
    return decorated_function


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-Id')
        user_type = request.headers.get('X-User-Type')
        
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_type = request.headers.get('X-User-Type')
        
        if user_type not in ['admin', 'super_admin']:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def require_super_admin(f):
    """Decorator to require super admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_type = request.headers.get('X-User-Type')
        
        if user_type != 'super_admin':
            return jsonify({'error': 'Super admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function
