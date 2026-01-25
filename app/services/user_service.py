from datetime import datetime
from app import db
from app.models.user import User


class UserService:
    """Service for user operations"""
    
    def get_all_users(self, page: int = 1, per_page: int = 20):
        """Get all users with pagination"""
        pagination = User.query.order_by(User.date_joined.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return pagination.items, pagination.total
    
    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID"""
        return User.query.get(user_id)
    
    def get_user_by_email(self, email: str) -> User:
        """Get user by email"""
        return User.query.filter_by(email=email).first()
    
    def create_user(self, first_name: str, last_name: str, email: str, 
                    password: str, verification_token: str = None,
                    token_expires_at: str = None) -> User:
        """Create a new user"""
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            verification_token=verification_token,
            token_expires_at=datetime.fromisoformat(token_expires_at) if token_expires_at else None,
            type='unverified',
            email_verified=False
        )
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    def update_user(self, user_id: int, data: dict) -> tuple:
        """Update user profile
        Returns: (User, email_changed: bool) tuple
        """
        user = self.get_user_by_id(user_id)
        
        if not user:
            return (None, False)
        
        email_changed = False
        
        if 'firstName' in data:
            user.first_name = data['firstName']
        if 'lastName' in data:
            user.last_name = data['lastName']
        if 'email' in data:
            new_email = data['email']
            # Check if email is already taken by another user
            existing_user = self.get_user_by_email(new_email)
            if existing_user and existing_user.user_id != user_id:
                raise ValueError('Email already in use')
            
            # If email is actually changing
            if user.email != new_email:
                email_changed = True
                user.email = new_email
                # Set user to unverified and email_verified to False
                # Only if user is not admin or super_admin
                if user.type not in ['admin', 'super_admin']:
                    user.type = 'unverified'
                user.email_verified = False
        
        db.session.commit()
        
        return (user, email_changed)
    
    def update_profile_image(self, user_id: int, image_url: str) -> User:
        """Update user profile image"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            return None
        
        user.profile_image_url = image_url
        db.session.commit()
        
        return user
    
    def verify_email(self, user_id: int) -> User:
        """Verify user email"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            return None
        
        user.email_verified = True
        # Only set type to 'normal' if user is currently 'unverified'
        # Preserve admin and super_admin types
        if user.type == 'unverified':
            user.type = 'normal'
        user.verification_token = None
        user.token_expires_at = None
        
        db.session.commit()
        
        return user
    
    def update_verification_token(self, user_id: int, token: str, expires_at: str) -> User:
        """Update user verification token"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            return None
        
        user.verification_token = token
        user.token_expires_at = datetime.fromisoformat(expires_at) if expires_at else None
        
        db.session.commit()
        
        return user
    
    def get_valid_verification_token(self, user_id: int) -> tuple:
        """Get valid verification token if exists and not expired
        Returns: (token, expires_at) or (None, None) if no valid token"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            return (None, None)
        
        # Check if token exists and is not expired
        if user.verification_token and user.token_expires_at:
            if user.token_expires_at > datetime.utcnow():
                # Token is still valid
                return (user.verification_token, user.token_expires_at)
        
        # Token doesn't exist or is expired
        return (None, None)
    
    def ban_user(self, user_id: int) -> User:
        """Ban a user"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            return None
        
        user.active = False
        db.session.commit()
        
        return user
    
    def unban_user(self, user_id: int) -> User:
        """Unban a user"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            return None
        
        user.active = True
        db.session.commit()
        
        return user
    
    def promote_to_admin(self, user_id: int) -> User:
        """Promote user to admin"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            return None
        
        user.type = 'admin'
        db.session.commit()
        
        return user
    
    def demote_from_admin(self, user_id: int) -> User:
        """Demote admin to normal user"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            return None
        
        # Only demote admin, not super_admin
        if user.type == 'admin':
            user.type = 'normal'
            db.session.commit()
        
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user (Super Admin only)"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            return False
        
        # Cannot delete super admin
        if user.type == 'super_admin':
            raise ValueError('Cannot delete super admin')
        
        db.session.delete(user)
        db.session.commit()
        
        return True