from flask import Flask
from flask_pymongo import PyMongo
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/college_voting')
mongo = PyMongo(app)

# Student data
student_data = {
    'student_id': '23251A6660',
    'name': 'Nithya',
    'mobile': '6303917738',
    'branch': 'CSE',
    'section': 'A',
    'has_voted': False,
    'is_admin': False
}

# Add test positions and candidates
positions = [
    {
        'title': 'Class Representative',
        'description': 'Represent your class in college matters'
    },
    {
        'title': 'Sports Captain',
        'description': 'Lead sports activities and represent in competitions'
    }
]

try:
    # Insert student
    result = mongo.db.users.insert_one(student_data)
    print(f"Student added successfully with ID: {result.inserted_id}")
    
    # Insert positions
    for position in positions:
        pos_result = mongo.db.positions.insert_one(position)
        print(f"Position added: {position['title']}")
        
        # Add some sample candidates for each position
        candidates = [
            {'name': 'Candidate 1', 'position_id': str(pos_result.inserted_id)},
            {'name': 'Candidate 2', 'position_id': str(pos_result.inserted_id)}
        ]
        for candidate in candidates:
            mongo.db.nominees.insert_one(candidate)
            print(f"Candidate added: {candidate['name']} for {position['title']}")
            
except Exception as e:
    print(f"Error: {e}") 