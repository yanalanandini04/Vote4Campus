# College Voting System

A secure and efficient voting system for college elections with features like OTP verification, real-time statistics, and admin dashboard.

## Features

- Student authentication with OTP verification
- One-time voting restriction
- Multiple positions and nominees
- Real-time voting statistics
- Admin dashboard with filters
- Mobile number verification
- Secure vote recording
- Local MongoDB database

## Prerequisites

- Python 3.7+
- pip (Python package installer)
- MongoDB Community Edition
- Twilio account (for OTP)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd college-voting-system
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install and start MongoDB:
   - For Windows: 
     - Download and install from [MongoDB website](https://www.mongodb.com/try/download/community)
     - MongoDB will run as a Windows service automatically
   - For Linux: 
     ```bash
     sudo apt-get install mongodb
     sudo systemctl start mongodb
     ```
   - For macOS: 
     ```bash
     brew install mongodb-community
     brew services start mongodb-community
     ```

5. Create a `.env` file in the project root with the following variables:
```
SECRET_KEY=your-secret-key
MONGO_URI=mongodb://localhost:27017/college_voting
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number
```

6. Run the application:
```bash
python app.py
```

## Usage

1. Access the application at `http://localhost:5000`
2. Students can login using their student ID and mobile number
3. OTP will be sent to the registered mobile number
4. After successful verification, students can cast their vote
5. Admin can access the dashboard at `/admin` to view statistics and voting details

## Admin Setup

1. Create an admin user in MongoDB:
```javascript
use college_voting
db.users.insertOne({
    student_id: 'ADMIN001',
    name: 'Admin User',
    mobile: '1234567890',
    branch: 'Admin',
    section: 'A',
    is_admin: true,
    has_voted: false
})
```

## Database Structure

The application uses the following MongoDB collections:

- `users`: Stores student and admin information
- `positions`: Stores available positions for voting
- `nominees`: Stores nominee information for each position
- `votes`: Stores voting records

## Security Features

- OTP verification for student authentication
- One-time voting restriction
- Admin-only access to voting statistics
- Secure session management
- MongoDB authentication
- Data validation and sanitization
- Local database security

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 