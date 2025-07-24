from flask import Flask
from flask_pymongo import PyMongo
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/college_voting'
mongo = PyMongo(app)

# User data
user_data = {
    'student_id': '23251A6660',
    'name': 'Nithya',
    'mobile': '6303917738',
    'branch': 'CSE',
    'section': 'A',
    'has_voted': False,
    'is_admin': False
}

try:
    # Add user
    result = mongo.db.users.insert_one(user_data)
    print(f"User added successfully with ID: {result.inserted_id}")
    
    # Verify user was added
    user = mongo.db.users.find_one({'student_id': '23251A6660'})
    if user:
        print("\nUser found in database:")
        print(f"Student ID: {user['student_id']}")
        print(f"Name: {user['name']}")
        print(f"Mobile: {user['mobile']}")
        print(f"Branch: {user['branch']}")
        print(f"Section: {user['section']}")
    else:
        print("Error: User not found after insertion!")

except Exception as e:
    print(f"Error: {e}") 

   