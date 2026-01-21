# seed.py
# Script to populate the database with initial test data

from app import create_app
from app.models import db
from app.models.user import User

# Test users data
SEED_USERS = [
    {
        'firstName': 'Super',
        'lastName': 'Admin',
        'email': 'superadmin@forum.com',
        'password': 'SuperAdmin123!',
        'userType': 'superadmin',
        'isActive': True
    },
    {
        'firstName': 'Admin',
        'lastName': 'User',
        'email': 'admin@forum.com',
        'password': 'AdminUser123!',
        'userType': 'admin',
        'isActive': True
    },
    {
        'firstName': 'John',
        'lastName': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'Password123!',
        'userType': 'normal_user',
        'isActive': True
    },
    {
        'firstName': 'Jane',
        'lastName': 'Smith',
        'email': 'jane.smith@example.com',
        'password': 'Password123!',
        'userType': 'normal_user',
        'isActive': True
    },
    {
        'firstName': 'Bob',
        'lastName': 'Wilson',
        'email': 'bob.wilson@example.com',
        'password': 'Password123!',
        'userType': 'unverified',
        'isActive': True
    },
    {
        'firstName': 'Banned',
        'lastName': 'User',
        'email': 'banned@example.com',
        'password': 'Password123!',
        'userType': 'normal_user',
        'isActive': False  # Banned user
    }
]


def seed_database():
    """Seed the database with initial users"""
    app = create_app()
    
    with app.app_context():
        print("🌱 Starting database seeding...")
        
        created_count = 0
        skipped_count = 0
        
        for user_data in SEED_USERS:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email']).first()
            
            if existing_user:
                print(f"  ⏭️  Skipped: {user_data['email']} (already exists)")
                skipped_count += 1
                continue
            
            # Create new user
            user = User(
                firstName=user_data['firstName'],
                lastName=user_data['lastName'],
                email=user_data['email'],
                userType=user_data['userType'],
                isActive=user_data['isActive']
            )
            user.set_password(user_data['password'])
            
            db.session.add(user)
            print(f"  ✅ Created: {user_data['email']} ({user_data['userType']})")
            created_count += 1
        
        db.session.commit()
        
        print(f"\n🎉 Seeding complete!")
        print(f"   Created: {created_count} users")
        print(f"   Skipped: {skipped_count} users")
        print(f"   Total in DB: {User.query.count()} users")


def clear_database():
    """Clear all users from the database (use with caution!)"""
    app = create_app()
    
    with app.app_context():
        count = User.query.count()
        User.query.delete()
        db.session.commit()
        print(f"🗑️  Deleted {count} users from the database")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--clear':
        clear_database()
    else:
        seed_database()
