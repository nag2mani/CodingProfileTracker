import os
import bcrypt
import requests
from flask_session import Session
from supabase import create_client, Client
from flask import Flask, request, redirect, url_for, session, render_template, flash
from leetcode_api import get_leetcode_data

app = Flask(__name__)

from dotenv import load_dotenv
load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Flask session config
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

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


@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' in session:
        # Fetch user details from Supabase
        response = supabase.from_('users').select('*').eq('id', session['user_id']).execute()
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


@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' in session and session.get('role') == 'teacher':
        # Fetch all students
        response = supabase.from_('users').select('*').eq('role', 'student').execute()
        students = response.data
        return render_template('teacher/dashboard.html', username=session.get('username'), students=students)
    flash('Access denied.', 'danger')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)