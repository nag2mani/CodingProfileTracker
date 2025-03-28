import os
import bcrypt
import uuid
from flask_wtf import CSRFProtect
from flask_session import Session
from datetime import datetime
from supabase import create_client, Client
from flask import Flask, request, redirect, url_for, session, render_template, flash, jsonify
from leetcode_api import get_leetcode_data
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Flask session config
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize session and CSRF protection
Session(app)
csrf = CSRFProtect(app)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    if 'user_id' in session:
        # Fetch user role from the database
        response = supabase.from_('users').select('role').eq('id', session['user_id']).execute()
        if response.data:
            role = response.data[0]['role']
            if role == 'student':
                return redirect(url_for('student_dashboard'))
            elif role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
        # If user role not found, redirect to login
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        leetcode = request.form.get('leetcode')
        github = request.form.get('github')

        # Check if user already exists
        response = supabase.from_('users').select('*').eq('email', email).execute()
        if response.data:
            flash('Email already exists!', 'danger')
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Prepare user data
        user_data = {
            'name': name,
            'email': email,
            'password': hashed_password.decode('utf-8'),
            'role': role
        }

        if role == 'student':
            user_data['leetcode'] = leetcode
            user_data['github'] = github

        # Insert user into database
        supabase.from_('users').insert(user_data).execute()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please fill out all fields.', 'danger')
            return redirect(url_for('login'))

        # Fetch user from database
        response = supabase.from_('users').select('*').eq('email', email).execute()

        if response.data:
            user = response.data[0]
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                session['user_id'] = user['id']
                session['username'] = user['name']
                session['role'] = user['role']  # Store role in session
                flash('Login successful!', 'success')

                # Redirect based on user role
                if user['role'] == 'student':
                    return redirect(url_for('student_dashboard'))
                elif user['role'] == 'teacher':
                    return redirect(url_for('teacher_dashboard'))
            else:
                flash('Invalid password', 'danger')
        else:
            flash('User not found', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ------------------- Student Dashboard -------------------

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' in session:
        user_id = session['user_id']

        # Fetch user details
        response = supabase.from_('users').select('*').eq('id', user_id).execute()
        if response.data:
            user = response.data[0]
            leetcode_data1 = {}

            try:
                url = user.get('leetcode')
                if url:
                    username = url.rstrip('/').split("/")[-1]
                    leetcode_data1 = get_leetcode_data(username) or {
                        'ranking': 'N/A',
                        'totalSolved': 0,
                        'totalQuestions': 0,
                        'easySolved': 0,
                        'totalEasy': 0,
                        'mediumSolved': 0,
                        'totalMedium': 0,
                        'hardSolved': 0,
                        'totalHard': 0,
                        'acceptanceRate': 0,
                        'contributionPoints': 0,
                        'reputation': 0,
                    }
                else:
                    leetcode_data1 = {
                        'ranking': 'No Link Provided',
                        'totalSolved': 0,
                        'totalQuestions': 0,
                        'easySolved': 0,
                        'totalEasy': 0,
                        'mediumSolved': 0,
                        'totalMedium': 0,
                        'hardSolved': 0,
                        'totalHard': 0,
                        'acceptanceRate': 0,
                        'contributionPoints': 0,
                        'reputation': 0,
                    }
            except Exception as e:
                print("Error:", e)

            
            return render_template('student/dashboard.html', user=user, leetcode_data1=leetcode_data1)

    flash('Please log in to access the dashboard.', 'warning')
    return redirect(url_for('login'))

@app.route('/student/assignments/')
def student_assignments():
    if 'user_id' in session:
        user_id = session['user_id']

        response = supabase.from_('users').select('*').eq('id', user_id).execute()
        if response.data:
            user = response.data[0]
            # Get all assignments
            assignments = supabase.from_('assignments') \
                .select('id, name, deadline, created_at') \
                .order('created_at', desc=True) \
                .execute().data

            # Get completion status for the logged-in student
            completed_assignments = supabase.from_('student_assignments') \
                .select('assignment_id, status') \
                .eq('student_id', user_id) \
                .execute().data

            # Convert to a dictionary for faster lookup
            status_map = {item['assignment_id']: item['status'] for item in completed_assignments}

            # Add status to the assignment list
            for assignment in assignments:
                assignment['status'] = status_map.get(assignment['id'], 'pending')

                # Get assignment questions
                questions = supabase.from_('assignment_questions') \
                    .select('question_number') \
                    .eq('assignment_id', assignment['id']) \
                    .execute().data

                assignment['assignment_questions'] = questions
            return render_template('student/assignments.html', user=user, assignments=assignments)

    flash('Please log in to access the dashboard.', 'warning')
    return redirect(url_for('login'))

@app.route('/student/complete_assignment/<assignment_id>', methods=['POST'])
def complete_assignment(assignment_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']

    # Validate assignment_id format
    try:
        uuid.UUID(assignment_id)
    except ValueError:
        return jsonify({'error': 'Invalid assignment ID'}), 400
    
    # Check if assignment exists
    assignment = supabase.from_('assignments') \
        .select('id') \
        .eq('id', assignment_id) \
        .execute()

    if not assignment.data:
        return jsonify({'error': 'Assignment not found'}), 404

    # Upsert to handle insert or update in one query
    response = supabase.from_('student_assignments').upsert({
        'assignment_id': assignment_id,
        'student_id': user_id,
        'status': 'completed',
        'submitted_at': datetime.now().isoformat()
    }).execute()

    if getattr(response, 'error', None):
        return jsonify({'error': 'Failed to mark assignment as completed'}), 500

    return jsonify({'success': 'Assignment marked as completed'}), 200

# ------------------- Teacher Dashboard -------------------

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' in session and session.get('role') == 'teacher':
        return render_template('teacher/dashboard.html', username=session.get('username'))
    
    flash('Access denied.', 'danger')
    return redirect(url_for('login'))

@app.route('/teacher/students')
def teacher_students():
    if 'user_id' in session and session.get('role') == 'teacher':
        students = supabase.from_('users').select('*').eq('role', 'student').execute().data

        # Fetch LeetCode rank for each student
        for student in students:
            leetcode_data = {}
            try:
                url = student.get('leetcode')
                if url:
                    username = url.rstrip('/').split("/")[-1]
                    leetcode_data = get_leetcode_data(username) or {}
                student['leetcode_rank'] = leetcode_data.get('ranking', 'N/A')
            except Exception as e:
                student['leetcode_rank'] = 'N/A'
                print(f"Error fetching LeetCode data for {student['name']}: {e}")

        # Sort students by LeetCode rank (convert 'N/A' to large number to push them to the end)
        students.sort(key=lambda x: int(x['leetcode_rank']) if x['leetcode_rank'] != 'N/A' else float('inf'))

        return render_template('teacher/students.html', students=students)

    flash('Access denied.', 'danger')
    return redirect(url_for('login'))



# ------------------- Assignments Page -------------------
@app.route('/teacher/assignments')
def assignments_page():
    if 'user_id' in session and session.get('role') == 'teacher':
        # Get all students
        total_students = supabase.from_('users').select('*').eq('role', 'student').execute().data
        total_students_count = len(total_students)

        # Get assignments created by the teacher
        assignments = supabase.from_('assignments').select('*').eq('created_by', session['user_id']).execute().data

        for assignment in assignments:
            # Count completed assignments
            completed_count = supabase.from_('student_assignments') \
                .select('id') \
                .eq('assignment_id', assignment['id']) \
                .eq('status', 'completed') \
                .execute().data

            assignment['completed_count'] = len(completed_count)
            assignment['total_students'] = total_students_count

            # Get all questions for the assignment
            questions = supabase.from_('assignment_questions') \
                .select('question_number') \
                .eq('assignment_id', assignment['id']) \
                .execute().data

            assignment['questions'] = [q['question_number'] for q in questions]

        return render_template('teacher/assignments.html', assignments=assignments)
    
    flash('Access denied.', 'danger')
    return redirect(url_for('login'))


@app.route('/teacher/create_assignment', methods=['POST'])
def create_assignment():
    if 'user_id' in session and session.get('role') == 'teacher':
        name = request.form.get('name')
        question_numbers = request.form.get('questions').split(',')
        deadline = request.form.get('deadline')

        assignment_id = str(uuid.uuid4())

        assignment_data = {
            'id': assignment_id,
            'name': name,
            'created_by': session['user_id'],
            'deadline': deadline,
            'created_at': datetime.now().isoformat()
        }

        supabase.from_('assignments').insert(assignment_data).execute()

        for q in question_numbers:
            question_data = {
                'id': str(uuid.uuid4()),
                'assignment_id': assignment_id,
                'question_number': int(q.strip())
            }
            supabase.from_('assignment_questions').insert(question_data).execute()

        flash('Assignment created!', 'success')
        return redirect(url_for('assignments_page'))  # Redirect to assignments page

    flash('Failed to create assignment.', 'danger')
    return redirect(url_for('assignments_page'))


@app.route('/teacher/delete_assignment/<assignment_id>', methods=['POST'])
def delete_assignment(assignment_id):
    if 'user_id' in session and session.get('role') == 'teacher':
        # Delete assignment and related data
        supabase.from_('assignments').delete().eq('id', assignment_id).execute()
        supabase.from_('assignment_questions').delete().eq('assignment_id', assignment_id).execute()
        flash('Assignment deleted!', 'success')
        return '', 204  # No content

    flash('Failed to delete assignment.', 'danger')
    return '', 400

if __name__ == '__main__':
    app.run(debug=True)