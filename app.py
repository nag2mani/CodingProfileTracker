import bcrypt
import requests
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, render_template, redirect, session, flash, url_for
from code_analyzer import CodeAnalyzer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['GEMINI_API_KEY'] = 'AIzaSyBPACYeOCfWLExbKVFd3r64IR3KhcVo-CQ'
app.secret_key = 'secret_key'  # Should be a secure random key in production
db = SQLAlchemy(app)

with app.app_context():  # Activate the app context
    code_analyzer = CodeAnalyzer()


# User model
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

# Create database tables
with app.app_context():
    db.create_all()

# Fetch LeetCode data
def get_leetcode_data(username):
    url = f"https://leetcode-stats-api.herokuapp.com/{username}"
    try:
        response = requests.get(url, timeout=5)
        print("Status of Response:", response.status_code)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        print("Error fetching LeetCode data:", e)
    return None

# Routes
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
        flash('Please login to access the dashboard.', 'danger')
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
    if 'email' not in session or session['role'] != 'teacher':
        flash('Please login as a teacher to access this page.', 'danger')
        return redirect('/login')
    return render_template('StudentList.html', students=students)

@app.route('/student/<int:student_id>')
def student_profile(student_id):
    if 'email' not in session or session['role'] != 'teacher':
        flash('Please login as a teacher to access this page.', 'danger')
        return redirect('/login')
    student = next((s for s in students if s["id"] == student_id), None)
    if student:
        return render_template('StudentProfile.html', student=student)
    return "Student not found", 404

# Fake problem data
problems = [
    {
        "id": "704",
        "name": "Binary Search Implementation",
        "link": "https://leetcode.com/problems/binary-search/",
        "platform": "LeetCode",
        "difficulty": "easy",
        "due_date": "2 days left",
        "status": "in-progress",
        "description": "Given a sorted array of integers and a target value, find the index of the target using binary search. If the target is not present, return -1."
    },
    {
        "id": "QST101",
        "name": "Quick Sort Algorithm",
        "link": "https://www.hackerrank.com/challenges/quicksort",
        "platform": "HackerRank",
        "difficulty": "medium",
        "due_date": "5 days left",
        "status": "not-started",
        "description": "Implement the quicksort algorithm to sort an array of integers in ascending order."
    },
    {
        "id": "GT202",
        "name": "Graph Traversal",
        "link": "https://codeforces.com/problemset/problem/202",
        "platform": "Codeforces",
        "difficulty": "hard",
        "due_date": "1 week left",
        "status": "completed",
        "description": "Perform a depth-first search (DFS) on a given graph to find all connected components."
    }
]

@app.route('/student_assignments')
def student_assignments():
    if 'email' not in session or session['role'] != 'student':
        flash('Please login as a student to access this page.', 'danger')
        return redirect('/login')
    return render_template('StudentAssignment.html', problems=problems)

@app.route('/problem/<problem_id>')
def problem_detail(problem_id):
    if 'email' not in session or session['role'] != 'student':
        flash('Please login as a student to access this page.', 'danger')
        return redirect('/login')
    problem = next((p for p in problems if p['id'] == problem_id), None)
    if not problem:
        return "Problem not found", 404
    return render_template('ProblemDetail.html', problem=problem)

@app.route('/problem/<problem_id>/submit', methods=['POST'])
def submit_code(problem_id):
    if 'email' not in session or session['role'] != 'student':
        flash('Please login as a student to access this page.', 'danger')
        return redirect('/login')
    
    problem = next((p for p in problems if p['id'] == problem_id), None)
    if not problem:
        return "Problem not found", 404
    
    code = request.form.get('code')
    if not code:
        flash('No code submitted.', 'danger')
        return redirect(url_for('problem_detail', problem_id=problem_id))
    
    # Prepare code data for analysis
    code_data = {
        'question_title': problem['name'],
        'question_description': problem['description'],
        'language': 'Python',  # Assuming Python for now; you can make this dynamic
        'code': code
    }
    
    try:
        # Analyze the code using CodeAnalyzer
        analysis_result = code_analyzer.analyze_code(code_data)
        # Store the analysis result in the session
        session[f'analysis_result_{problem_id}'] = analysis_result
        flash('Code submitted and analyzed successfully!', 'success')
    except Exception as e:
        flash(f'Code analysis failed: {str(e)}', 'danger')
    
    return redirect(url_for('problem_detail', problem_id=problem_id))


# Fake assignment data
assignments = [
    {
        "id": "AST001",
        "name": "Binary Search Trees",
        "due_date": "Mar 15, 2025",
        "completion_rate": 60,
        "status": "active",
        "problems": [
            {"id": "704", "name": "Binary Search Implementation", "link": "https://leetcode.com/problems/binary-search/", "platform": "LeetCode", "difficulty": "easy"}
        ]
    },
    {
        "id": "AST002",
        "name": "Graph Algorithms",
        "due_date": "Mar 20, 2025",
        "completion_rate": 30,
        "status": "active",
        "problems": [
            {"id": "GPH101", "name": "Graph Traversal", "link": "https://codeforces.com/problemset/problem/202", "platform": "Codeforces", "difficulty": "hard"}
        ]
    },
    {
        "id": "AST003",
        "name": "Dynamic Programming",
        "due_date": "Mar 25, 2025",
        "completion_rate": 10,
        "status": "due-soon",
        "problems": [
            {"id": "DP202", "name": "Knapsack Problem", "link": "https://leetcode.com/problems/0-1-knapsack/", "platform": "LeetCode", "difficulty": "medium"}
        ]
    }
]

# Fake student submission data
submissions = {
    "704": [
        {"student": "Alice", "solved": True, "time_complexity": "O(log n)", "space_complexity": "O(1)", "execution_time_ms": 25, "code_length": 150},
        {"student": "Bob", "solved": False, "time_complexity": "O(n)", "space_complexity": "O(n)", "execution_time_ms": 50, "code_length": 200},
        {"student": "Charlie", "solved": True, "time_complexity": "O(log n)", "space_complexity": "O(1)", "execution_time_ms": 20, "code_length": 130}
    ],
    "GPH101": [
        {"student": "Alice", "solved": True, "time_complexity": "O(V + E)", "space_complexity": "O(V)", "execution_time_ms": 80, "code_length": 300},
        {"student": "Bob", "solved": False, "time_complexity": "O(V^2)", "space_complexity": "O(V^2)", "execution_time_ms": 120, "code_length": 400}
    ],
    "DP202": [
        {"student": "Charlie", "solved": False, "time_complexity": "O(2^n)", "space_complexity": "O(n)", "execution_time_ms": 200, "code_length": 250}
    ]
}

@app.route('/teacher_assignments')
def teacher_assignments():
    if 'email' not in session or session['role'] != 'teacher':
        flash('Please login as a teacher to access this page.', 'danger')
        return redirect('/login')
    return render_template('AssignmentPage.html', assignments=assignments)

@app.route('/assignment/<assignment_id>')
def assignment_detail_teacher(assignment_id):
    if 'email' not in session or session['role'] != 'teacher':
        flash('Please login as a teacher to access this page.', 'danger')
        return redirect('/login')
    assignment = next((a for a in assignments if a['id'] == assignment_id), None)
    if not assignment:
        return "Assignment not found", 404
    # Get submission data for the first problem in the assignment (for simplicity)
    problem_id = assignment['problems'][0]['id']
    submission_data = submissions.get(problem_id, [])
    solved_count = sum(1 for s in submission_data if s['solved'])
    total_students = len(submission_data)
    return render_template('AssignmentDetailTeacher.html', assignment=assignment, submission_data=submission_data, solved_count=solved_count, total_students=total_students)

@app.route('/assignment/<assignment_id>/update_deadline', methods=['POST'])
def update_deadline(assignment_id):
    if 'email' not in session or session['role'] != 'teacher':
        flash('Please login as a teacher to access this page.', 'danger')
        return redirect('/login')
    new_date = request.form.get('new-deadline')
    if new_date:
        assignment = next((a for a in assignments if a['id'] == assignment_id), None)
        if assignment:
            assignment['due_date'] = new_date
            flash('Deadline updated successfully!', 'success')
            return redirect(url_for('teacher_assignments'))
    flash('Failed to update deadline.', 'danger')
    return redirect(url_for('teacher_assignments'))

@app.route('/assignment/<assignment_id>/archive', methods=['POST'])
def archive_assignment(assignment_id):
    if 'email' not in session or session['role'] != 'teacher':
        flash('Please login as a teacher to access this page.', 'danger')
        return redirect('/login')
    assignment = next((a for a in assignments if a['id'] == assignment_id), None)
    if assignment:
        assignment['status'] = 'archived'
        flash('Assignment archived successfully!', 'success')
    else:
        flash('Assignment not found.', 'danger')
    return redirect(url_for('teacher_assignments'))

@app.route('/assignment/<assignment_id>/delete', methods=['POST'])
def delete_assignment(assignment_id):
    if 'email' not in session or session['role'] != 'teacher':
        flash('Please login as a teacher to access this page.', 'danger')
        return redirect('/login')
    global assignments
    assignments = [a for a in assignments if a['id'] != assignment_id]
    flash('Assignment deleted successfully!', 'success')
    return redirect(url_for('teacher_assignments'))

@app.route('/analytics')
def student_analysis():
    if 'email' not in session or session['role'] != 'teacher':
        flash('Please login as a student to access this page.', 'danger')
        return redirect('/login')
    return render_template('AnalyticsPage.html')

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'email' not in session:
        flash('Please login to access this page.', 'danger')
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