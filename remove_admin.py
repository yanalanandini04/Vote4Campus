from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['college_voting']

# Remove admin0001 user
result = db.users.delete_one({'student_id': 'ADMIN0001'})

if result.deleted_count > 0:
    print("Admin0001 user has been removed successfully.")
else:
    print("Admin0001 user was not found in the database.") 