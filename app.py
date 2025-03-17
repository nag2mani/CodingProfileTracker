import bcrypt
import requests
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, render_template, redirect, session, flash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'
    leetcode = db.Column(db.String(200), nullable=True)
    codeforces = db.Column(db.String(200), nullable=True)
    linkedin = db.Column(db.String(200), nullable=True)
    github = db.Column(db.String(200), nullable=True)

    def __init__(self, name, email, password, role):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.role = role
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

with app.app_context():
    db.create_all()

def get_leetcode_data(username):
    url = f"https://leetcode-stats-api.herokuapp.com/{username}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['full-name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # student or teacher

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect('/register')

        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect('/login')
    
    return render_template('SignupPage.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect('/dashboard')
        else:
            flash('Invalid email or password', 'danger')
            return redirect('/login')
    
    return render_template('LoginPage.html')

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect('/login')
    user = User.query.filter_by(email=session['email']).first()
    if user.role == 'teacher':
        return render_template('TeacherDashboard.html')
    else:
        leetcode_data = None
        if user.leetcode:
            username = user.leetcode.split("/")[-2]  # Extract LeetCode username from URL
            leetcode_data = get_leetcode_data(username)
        
        return render_template('StudentDashboard.html', user=user, leetcode_data=leetcode_data)

# Dummy student data (replace with actual database queries)
students = [
    {"id": 1, "name": "Alice Cooper", "problems_solved": 156, "streak": "12 days", "rank": "#1", "last_active": "2 mins ago", "status": "Active"},
    {"id": 2, "name": "Bob Smith", "problems_solved": 143, "streak": "8 days", "rank": "#2", "last_active": "15 mins ago", "status": "Active"},
    {"id": 3, "name": "Carol Davis", "problems_solved": 128, "streak": "5 days", "rank": "#3", "last_active": "1 hour ago", "status": "Inactive"},
    {"id": 4, "name": "David Wilson", "problems_solved": 112, "streak": "3 days", "rank": "#4", "last_active": "3 hours ago", "status": "Active"},
    {"id": 5, "name": "Eve Johnson", "problems_solved": 98, "streak": "1 day", "rank": "#5", "last_active": "5 hours ago", "status": "Inactive"},
    {"id": 6, "name": "Alice Cooper", "problems_solved": 156, "streak": "12 days", "rank": "#1", "last_active": "2 mins ago", "status": "Active"},
    {"id": 7, "name": "Bob Smith", "problems_solved": 143, "streak": "8 days", "rank": "#2", "last_active": "15 mins ago", "status": "Active"},
    {"id": 8, "name": "Carol Davis", "problems_solved": 128, "streak": "5 days", "rank": "#3", "last_active": "1 hour ago", "status": "Inactive"},
    {"id": 9, "name": "David Wilson", "problems_solved": 112, "streak": "3 days", "rank": "#4", "last_active": "3 hours ago", "status": "Active"},
    {"id": 10, "name": "Eve Johnson", "problems_solved": 98, "streak": "1 day", "rank": "#5", "last_active": "5 hours ago", "status": "Inactive"},
    {"id": 11, "name": "Alice Cooper", "problems_solved": 156, "streak": "12 days", "rank": "#1", "last_active": "2 mins ago", "status": "Active"},
    {"id": 12, "name": "Bob Smith", "problems_solved": 143, "streak": "8 days", "rank": "#2", "last_active": "15 mins ago", "status": "Active"},
    {"id": 13, "name": "Carol Davis", "problems_solved": 128, "streak": "5 days", "rank": "#3", "last_active": "1 hour ago", "status": "Inactive"},
    {"id": 14, "name": "David Wilson", "problems_solved": 112, "streak": "3 days", "rank": "#4", "last_active": "3 hours ago", "status": "Active"},
    {"id": 15, "name": "Eve Johnson", "problems_solved": 98, "streak": "1 day", "rank": "#5", "last_active": "5 hours ago", "status": "Inactive"},
]

@app.route('/students')
def student_list():
    return render_template('StudentList.html', students=students)

@app.route('/student/<int:student_id>')
def student_profile(student_id):
    # Find the student by ID (replace with actual database query)
    student = next((s for s in students if s["id"] == student_id), None)
    if student:
        return render_template('StudentProfile.html', student=student)
    return "Student not found", 404

@app.route('/assignment')
def assignment():
    return render_template('AssignmentPage.html')

@app.route('/student_assignment')
def student_assignment():
    return render_template('StudentAssignment.html')

@app.route('/analytics')
def studentAnalysis():
    return render_template('AnalyticsPage.html')

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'email' not in session:
        return redirect('/login')
    
    user = User.query.filter_by(email=session['email']).first()
    if request.method == 'POST':
        user.leetcode = request.form['leetcode']
        user.codeforces = request.form['codeforces']
        user.linkedin = request.form['linkedin']
        user.github = request.form['github']
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect('/dashboard')
    
    return render_template('EditProfile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
