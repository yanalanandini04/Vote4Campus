from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from dotenv import load_dotenv
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length
import os
import random
import uuid

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-super-secret-key-here'  # Hardcoded for testing
app.config['MONGO_URI'] = 'mongodb://localhost:27017/college_voting'  # Hardcoded for testing
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder for storing uploaded images

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

mongo = PyMongo(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Removed Twilio integration as per user request

# WTForms
class LoginForm(FlaskForm):
    student_id = StringField('Student ID', validators=[DataRequired(), Length(min=10, max=10)])
    mobile_number = StringField('Mobile Number', validators=[DataRequired(), Length(min=10, max=10)])
    user_type = SelectField('Login As', choices=[('user', 'Student'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Login')

class OTPForm(FlaskForm):
    otp = StringField('OTP', validators=[DataRequired(), Length(min=6, max=6)])
    student_id = StringField('Student ID')  # Hidden field
    submit = SubmitField('Verify OTP')

# User model
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.student_id = user_data['student_id']
        self.name = user_data['name']
        self.mobile = user_data['mobile']
        self.branch = user_data['branch']
        self.section = user_data['section']
        self.has_voted = user_data.get('has_voted', False)
        self.is_admin = user_data.get('is_admin', False)

    @staticmethod
    def get(user_id):
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        return User(user_data) if user_data else None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    otp_form = OTPForm()

    if request.method == 'POST':
        print("Login POST request received")  # Debug print
        print(f"Form validate_on_submit: {form.validate_on_submit()}")  # Debug print
        if form.validate_on_submit():
            try:
                student_id = form.student_id.data.strip()
                mobile = form.mobile_number.data.strip()
                user_type = form.user_type.data

                user_data = mongo.db.users.find_one({
                    'student_id': student_id,
                    'mobile': mobile
                })

                if user_data:
                    # Check if user is trying to login as admin
                    if user_type == 'admin' and not user_data.get('is_admin', False):
                        flash('You do not have admin privileges.', 'danger')
                        return render_template('login.html', form=form, otp_form=otp_form)

                    otp = str(random.randint(100000, 999999))
                    session['otp'] = otp
                    session['student_id'] = student_id
                    session['user_type'] = user_type
                    print(f"✅ OTP for {student_id}: {otp}")  # For testing only
                    flash('OTP has been sent to your registered mobile number.', 'success')
                    return render_template('login.html', form=form, otp_form=otp_form, otp_sent=True)

                flash('Invalid student ID or mobile number.', 'danger')
            except Exception as e:
                print(f"Error in login route: {str(e)}")
                flash('An error occurred. Please try again.', 'danger')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'warning')

    return render_template('login.html', form=form, otp_form=otp_form)

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    print("OTP verification started...")
    form = OTPForm()
    
    try:
        if form.validate_on_submit():
            print("Form validated")
            otp = form.otp.data.strip()
            student_id = session.get('student_id')
            stored_otp = session.get('otp')
            user_type = session.get('user_type')
            
            print(f"Entered OTP: {otp}")
            print(f"Stored OTP: {stored_otp}")
            print(f"Student ID: {student_id}")
            
            if not student_id or not stored_otp:
                print("Session data missing")
                return jsonify({'success': False, 'message': 'Session expired. Please login again.'})
            
            if otp == stored_otp:
                print("OTP matched")
                user_data = mongo.db.users.find_one({'student_id': student_id})
                if user_data:
                    user = User(user_data)
                    login_user(user)
                    # Clear session data
                    session.pop('otp', None)
                    session.pop('student_id', None)
                    session.pop('user_type', None)
                    print("Login successful, redirecting...")
                    
                    # Redirect based on user type
                    if user_type == 'admin':
                        return jsonify({'success': True, 'redirect': url_for('admin_dashboard')})
                    else:
                        return jsonify({'success': True, 'redirect': url_for('voting_page')})
            
            print("Invalid OTP")
            return jsonify({'success': False, 'message': 'Invalid OTP. Please try again.'})
        
        print("Form validation failed")
        return jsonify({'success': False, 'message': 'Please enter a valid OTP.'})
    
    except Exception as e:
        import traceback
        print("Error in verify_otp:")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'})

@app.route('/voting')
@login_required
def voting_page():
    try:
        # Prevent admin from voting
        if current_user.is_admin:
            flash('Admins are not allowed to vote.', 'warning')
            return redirect(url_for('index'))

        if current_user.has_voted:
            flash('You have already voted!')
            return redirect(url_for('index'))

        # Get positions and candidates
        positions = list(mongo.db.positions.find())
        for position in positions:
            position['_id'] = str(position['_id'])
            candidates = list(mongo.db.nominees.find({'position_id': str(position['_id'])}))
            for candidate in candidates:
                candidate['_id'] = str(candidate['_id'])
            position['candidates'] = candidates

        return render_template('voting.html', positions=positions)
    except Exception as e:
        print(f"Error in voting_page: {str(e)}")  # Add logging
        flash('An error occurred while loading the voting page. Please try again.', 'danger')
        return redirect(url_for('index'))

@app.route('/submit_vote', methods=['POST'])
@login_required
def submit_vote():
    try:
        # Prevent admin from voting
        if current_user.is_admin:
            return jsonify({'success': False, 'message': 'Admins are not allowed to vote.'})

        if current_user.has_voted:
            return jsonify({'success': False, 'message': 'You have already voted!'})

        # Get votes from request
        votes = request.get_json()
        if not votes:
            return jsonify({'success': False, 'message': 'No votes received.'})

        # Validate that all positions have been voted for
        all_positions = list(mongo.db.positions.find())
        if len(votes) != len(all_positions):
            return jsonify({
                'success': False, 
                'message': f'Please vote for all positions. Expected {len(all_positions)} positions, received {len(votes)}.'
            })

        # Double-check if user has already voted
        user = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
        if user.get('has_voted', False):
            return jsonify({'success': False, 'message': 'You have already voted!'})

        # Process votes
        for position_id, nominee_id in votes.items():
            # Validate position and nominee exist
            position = mongo.db.positions.find_one({'_id': ObjectId(position_id)})
            nominee = mongo.db.nominees.find_one({'_id': ObjectId(nominee_id)})
            
            if not position:
                return jsonify({'success': False, 'message': f'Invalid position ID: {position_id}'})
            if not nominee:
                return jsonify({'success': False, 'message': f'Invalid nominee ID: {nominee_id}'})
            if nominee.get('position_id') != str(position['_id']):
                return jsonify({'success': False, 'message': f'Nominee {nominee_id} does not belong to position {position_id}'})

            # Record vote
            vote = {
                'user_id': current_user.id,
                'student_id': current_user.student_id,
                'position_id': position_id,
                'nominee_id': nominee_id,
                'timestamp': datetime.utcnow(),
                'branch': current_user.branch,
                'section': current_user.section
            }
            mongo.db.votes.insert_one(vote)

        # Update user's voting status
        mongo.db.users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': {'has_voted': True, 'voted_at': datetime.utcnow()}}
        )

        return jsonify({
            'success': True, 
            'message': 'Vote submitted successfully!', 
            'redirect': url_for('index')
        })

    except Exception as e:
        print(f"Error in submit_vote: {str(e)}")  # Add logging
        return jsonify({
            'success': False, 
            'message': 'An error occurred while submitting your vote. Please try again.'
        })

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))

    # Get all users with their voting status, excluding admins
    users = list(mongo.db.users.find({'is_admin': {'$ne': True}}))
    total_registered = len(users)  # Total number of registered students
    
    # Get actual votes cast
    total_votes_cast = len(mongo.db.votes.distinct('student_id'))  # Count of unique voters
    
    # Add vote IDs to users who have voted
    for user in users:
        if user.get('has_voted'):
            vote = mongo.db.votes.find_one({'student_id': user['student_id']})
            if vote:
                user['vote_id'] = str(vote['_id'])
    
    positions = list(mongo.db.positions.find())
    branches = mongo.db.users.distinct('branch', {'is_admin': {'$ne': True}})
    sections = mongo.db.users.distinct('section', {'is_admin': {'$ne': True}})

    # Get votes per branch (only counting actual votes)
    branch_stats = {}
    for branch in branches:
        # Count unique voters per branch
        branch_voters = mongo.db.votes.distinct('student_id', {'branch': branch})
        branch_votes = len(branch_voters)
        # Count total students in branch
        branch_total = mongo.db.users.count_documents({'branch': branch, 'is_admin': {'$ne': True}})
        branch_stats[branch] = {
            'total_users': branch_total,
            'voted': branch_votes,
            'percentage': round((branch_votes / branch_total * 100) if branch_total > 0 else 0, 2)
        }

    # Get votes per section (only counting actual votes)
    section_stats = {}
    for section in sections:
        # Count unique voters per section
        section_voters = mongo.db.votes.distinct('student_id', {'section': section})
        section_votes = len(section_voters)
        # Count total students in section
        section_total = mongo.db.users.count_documents({'section': section, 'is_admin': {'$ne': True}})
        section_stats[section] = {
            'total_users': section_total,
            'voted': section_votes,
            'percentage': round((section_votes / section_total * 100) if section_total > 0 else 0, 2)
        }

    # Get detailed candidate statistics
    for position in positions:
        candidates = list(mongo.db.nominees.find({'position_id': str(position['_id'])}))
        for candidate in candidates:
            # Get total votes for this candidate
            candidate_votes = mongo.db.votes.count_documents({'nominee_id': str(candidate['_id'])})
            
            # Get votes by branch for this candidate
            branch_votes = {}
            for branch in branches:
                branch_votes[branch] = mongo.db.votes.count_documents({
                    'nominee_id': str(candidate['_id']),
                    'branch': branch
                })
            
            candidate['votes'] = candidate_votes
            candidate['branch_votes'] = branch_votes
            # Calculate percentage based on total actual votes cast
            candidate['percentage'] = round((candidate_votes / total_votes_cast * 100) if total_votes_cast > 0 else 0, 2)
        
        position['candidates'] = candidates

    # Get list of users who haven't voted (excluding admins)
    non_voters = list(mongo.db.users.find({
        'is_admin': {'$ne': True},
        'student_id': {'$nin': mongo.db.votes.distinct('student_id')}  # Exclude students who have voted
    }))
    for user in non_voters:
        user['_id'] = str(user['_id'])

    return render_template('admin.html',
                         users=users,
                         positions=positions,
                         branches=branches,
                         sections=sections,
                         total_voters=total_registered,  # Total registered students
                         total_votes=total_votes_cast,   # Total actual votes cast
                         branch_stats=branch_stats,
                         section_stats=section_stats,
                         non_voters=non_voters)

@app.route('/admin/voting_stats')
@login_required
def voting_stats():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'})

    branch = request.args.get('branch')
    section = request.args.get('section')

    query = {}
    if branch:
        query['branch'] = branch
    if section:
        query['section'] = section

    users = list(mongo.db.users.find(query))
    voted = sum(1 for user in users if user.get('has_voted', False))

    return jsonify({
        'total': len(users),
        'voted': voted,
        'not_voted': len(users) - voted
    })

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/add_position', methods=['POST'])
@login_required
def add_position():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.json
        title = data.get('title')
        
        if not title:
            return jsonify({'success': False, 'message': 'Position title is required'})
        
        position = {
            'title': title,
            'created_at': datetime.utcnow()
        }
        
        result = mongo.db.positions.insert_one(position)
        return jsonify({
            'success': True,
            'message': 'Position added successfully',
            'position_id': str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/add_candidate', methods=['POST'])
@login_required
def add_candidate():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.json
        required_fields = ['position_id', 'name', 'branch', 'section']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'})
        
        # Validate position exists
        position = mongo.db.positions.find_one({'_id': ObjectId(data['position_id'])})
        if not position:
            return jsonify({'success': False, 'message': 'Invalid position'})
        
        # Handle image upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Generate unique filename
                filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_url = f'/static/uploads/{filename}'
        
        candidate = {
            'position_id': str(position['_id']),
            'name': data['name'],
            'branch': data['branch'],
            'section': data['section'],
            'description': data.get('description', ''),
            'image_url': image_url,
            'created_at': datetime.utcnow()
        }
        
        result = mongo.db.nominees.insert_one(candidate)
        return jsonify({
            'success': True,
            'message': 'Candidate added successfully',
            'candidate_id': str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/export_voters')
@login_required
def export_voters():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        voters = list(mongo.db.users.find())
        
        # Create CSV content
        csv_content = "Student ID,Name,Branch,Section,Voting Status,Voted At\n"
        for voter in voters:
            voted_at = voter.get('voted_at', '').strftime('%Y-%m-%d %H:%M:%S') if voter.get('voted_at') else ''
            csv_content += f"{voter['student_id']},{voter['name']},{voter['branch']},{voter['section']},{'Voted' if voter.get('has_voted') else 'Not Voted'},{voted_at}\n"
        
        # Create response with CSV file
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=voters_list.csv'
        return response
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/delete_position/<position_id>', methods=['DELETE'])
@login_required
def delete_position(position_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        # Delete position and associated nominees
        mongo.db.positions.delete_one({'_id': ObjectId(position_id)})
        mongo.db.nominees.delete_many({'position_id': position_id})
        return jsonify({'success': True, 'message': 'Position deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/delete_candidate/<candidate_id>', methods=['DELETE'])
@login_required
def delete_candidate(candidate_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        # Delete candidate and associated votes
        mongo.db.nominees.delete_one({'_id': ObjectId(candidate_id)})
        mongo.db.votes.delete_many({'nominee_id': candidate_id})
        return jsonify({'success': True, 'message': 'Candidate deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/add_student', methods=['POST'])
@login_required
def add_student():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.json
        required_fields = ['student_id', 'name', 'mobile', 'branch', 'section']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'})
        
        # Check if student already exists
        existing_student = mongo.db.users.find_one({'student_id': data['student_id']})
        if existing_student:
            return jsonify({'success': False, 'message': 'Student ID already exists'})
        
        student = {
            'student_id': data['student_id'],
            'name': data['name'],
            'mobile': data['mobile'],
            'branch': data['branch'],
            'section': data['section'],
            'has_voted': False,
            'is_admin': False,
            'created_at': datetime.utcnow()
        }
        
        result = mongo.db.users.insert_one(student)
        return jsonify({
            'success': True,
            'message': 'Student added successfully',
            'student_id': str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/delete_student/<student_id>', methods=['DELETE'])
@login_required
def delete_student(student_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        # Get the student's votes before deleting
        student_votes = list(mongo.db.votes.find({'student_id': student_id}))
        
        # Delete the student
        delete_result = mongo.db.users.delete_one({'student_id': student_id})
        
        if delete_result.deleted_count > 0:
            # Delete all votes associated with this student
            mongo.db.votes.delete_many({'student_id': student_id})
            
            # Update vote counts for affected candidates
            for vote in student_votes:
                # Update candidate vote count
                mongo.db.nominees.update_one(
                    {'_id': ObjectId(vote['nominee_id'])},
                    {'$inc': {'votes': -1}}
                )
            
            return jsonify({'success': True, 'message': 'Student and their votes deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Student not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/delete_vote/<vote_id>', methods=['DELETE'])
@login_required
def delete_vote(vote_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        # Get the vote details before deleting
        vote = mongo.db.votes.find_one({'_id': ObjectId(vote_id)})
        if not vote:
            return jsonify({'success': False, 'message': 'Vote not found'})

        # Get the user to check if they are an admin
        user = mongo.db.users.find_one({'student_id': vote['student_id']})
        if user and user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Cannot delete admin votes'})

        # Delete all votes for this student
        mongo.db.votes.delete_many({'student_id': vote['student_id']})
        
        # Update user's voting status
        mongo.db.users.update_one(
            {'student_id': vote['student_id']},
            {'$set': {'has_voted': False, 'voted_at': None}}
        )
        
        return jsonify({'success': True, 'message': 'Vote deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/delete_all_votes', methods=['DELETE'])
@login_required
def delete_all_votes():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        mongo.db.votes.delete_many({})
        mongo.db.users.update_many({}, {'$set': {'has_voted': False}})
        return jsonify({'success': True, 'message': 'All votes deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/set_voting_schedule', methods=['POST'])
@login_required
def set_voting_schedule():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.get_json()
        
        # Parse dates and times
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        # Validate dates
        if start_date > end_date:
            return jsonify({'success': False, 'message': 'Start date cannot be after end date'})
        
        # Convert to datetime objects and then to strings for MongoDB storage
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)
        
        # Update or insert schedule
        mongo.db.voting_schedule.update_one(
            {'_id': 'current_schedule'},
            {
                '$set': {
                    'start_date': start_datetime.strftime('%Y-%m-%d'),
                    'end_date': end_datetime.strftime('%Y-%m-%d'),
                    'start_time': start_time.strftime('%H:%M'),
                    'end_time': end_time.strftime('%H:%M')
                }
            },
            upsert=True
        )
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/get_voting_schedule', methods=['GET'])
@login_required
def get_voting_schedule():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        schedule = mongo.db.voting_schedule.find_one({'_id': 'current_schedule'})
        if schedule:
            # Convert datetime objects to strings
            return jsonify({
                'success': True,
                'schedule': {
                    'start_date': schedule['start_date'],
                    'end_date': schedule['end_date'],
                    'start_time': schedule['start_time'],
                    'end_time': schedule['end_time']
                }
            })
        return jsonify({'success': True, 'schedule': None})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_voting_schedule')
@login_required
def get_voting_schedule_student():
    try:
        schedule = mongo.db.voting_schedule.find_one({'_id': 'current_schedule'})
        if schedule:
            # Convert datetime objects to strings
            return jsonify({
                'success': True,
                'schedule': {
                    'start_date': schedule['start_date'].strftime('%Y-%m-%d') if isinstance(schedule['start_date'], datetime) else schedule['start_date'],
                    'end_date': schedule['end_date'].strftime('%Y-%m-%d') if isinstance(schedule['end_date'], datetime) else schedule['end_date'],
                    'start_time': schedule['start_time'].strftime('%H:%M') if isinstance(schedule['start_time'], datetime) else schedule['start_time'],
                    'end_time': schedule['end_time'].strftime('%H:%M') if isinstance(schedule['end_time'], datetime) else schedule['end_time']
                }
            })
        return jsonify({'success': True, 'schedule': None})
    except Exception as e:
        print(f"Error in get_voting_schedule: {str(e)}")  # Add logging
        return jsonify({'success': False, 'message': str(e)})

@app.route('/check_voting_status')
@login_required
def check_voting_status():
    try:
        if not is_voting_active():
            schedule = mongo.db.voting_schedule.find_one({'_id': 'current_schedule'})
            if schedule:
                # Format the schedule dates and times
                start_date = schedule['start_date'].strftime('%Y-%m-%d') if isinstance(schedule['start_date'], datetime) else schedule['start_date']
                end_date = schedule['end_date'].strftime('%Y-%m-%d') if isinstance(schedule['end_date'], datetime) else schedule['end_date']
                start_time = schedule['start_time'].strftime('%H:%M') if isinstance(schedule['start_time'], datetime) else schedule['start_time']
                end_time = schedule['end_time'].strftime('%H:%M') if isinstance(schedule['end_time'], datetime) else schedule['end_time']
                
                return jsonify({
                    'is_active': False,
                    'message': f'Voting is not active. Voting period: {start_date} to {end_date}, {start_time} to {end_time}'
                })
            return jsonify({
                'is_active': False,
                'message': 'Voting schedule has not been set.'
            })
        return jsonify({'is_active': True})
    except Exception as e:
        print(f"Error in check_voting_status: {str(e)}")  # Add logging
        return jsonify({'is_active': False, 'message': str(e)})

def is_voting_active():
    """Check if voting is currently active based on schedule"""
    try:
        schedule = mongo.db.voting_schedule.find_one({'_id': 'current_schedule'})
        if not schedule:
            return False
        
        now = datetime.utcnow()
        current_date = now.date()
        current_time = now.time()
        
        # Handle both datetime objects and string formats
        if isinstance(schedule['start_date'], str):
            start_date = datetime.strptime(schedule['start_date'], '%Y-%m-%d').date()
        else:
            start_date = schedule['start_date'].date()
            
        if isinstance(schedule['end_date'], str):
            end_date = datetime.strptime(schedule['end_date'], '%Y-%m-%d').date()
        else:
            end_date = schedule['end_date'].date()
            
        if isinstance(schedule['start_time'], str):
            start_time = datetime.strptime(schedule['start_time'], '%H:%M').time()
        else:
            start_time = schedule['start_time'].time()
            
        if isinstance(schedule['end_time'], str):
            end_time = datetime.strptime(schedule['end_time'], '%H:%M').time()
        else:
            end_time = schedule['end_time'].time()
        
        if start_date <= current_date <= end_date:
            if start_date == current_date and current_time < start_time:
                return False
            if end_date == current_date and current_time > end_time:
                return False
            return True
        return False
    except Exception as e:
        print(f"Error in is_voting_active: {str(e)}")  # Add logging
        return False

if __name__ == '__main__':
    try:
        # Test MongoDB connection
        mongo.db.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Create indexes
        mongo.db.users.create_index('student_id', unique=True)
        mongo.db.users.create_index('mobile')
        mongo.db.votes.create_index([('user_id', 1), ('nominee_id', 1)])
        
        # Start Flask app
        print("Starting Flask app...")
        try:
            app.run(debug=False, use_reloader=False, host='127.0.0.1', port=8000)
        except OSError as e:
            print(f"Socket error occurred: {e}")
            print("Try running the app with a production WSGI server like Gunicorn.")
    except Exception as e:
        print(f"❌ Error: {e}")
