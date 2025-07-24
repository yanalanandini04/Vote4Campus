from pymongo import MongoClient
from datetime import datetime

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['college_voting']

# Admin user details
admin_user = {
    'student_id': 'ADMIN00100',
    'name': 'Admin User',
    'mobile': '9999999999',
    'branch': 'ADMIN',
    'section': 'A',
    'is_admin': True,
    'has_voted': False,
    'created_at': datetime.utcnow()
}

# Check if admin already exists
existing_admin = db.users.find_one({'student_id': admin_user['student_id']})

if existing_admin:
    print("Admin user already exists!")
    print("Admin credentials:")
    print(f"Student ID: {admin_user['student_id']}")
    print(f"Mobile: {admin_user['mobile']}")
else:
    # Insert admin user
    result = db.users.insert_one(admin_user)
    print("Admin user created successfully!")
    print("\nAdmin credentials:")
    print(f"Student ID: {admin_user['student_id']}")
    print(f"Mobile: {admin_user['mobile']}")
    print("\nPlease use these credentials to login as admin.") 