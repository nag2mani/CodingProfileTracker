import os
import uuid
import statistics
from flask_wtf import CSRFProtect
from flask_session import Session
from datetime import datetime
from supabase import create_client, Client
from flask import Flask, request, redirect, url_for, session, render_template, flash, jsonify
from leetcode_api import get_leetcode_data
from supabase import create_client, Client
from dotenv import load_dotenv
from collections import Counter
import requests

load_dotenv()
app = Flask(__name__)

# app.secret_key = os.getenv("SECRET_KEY")
app.secret_key = os.environ.get('SECRET_KEY') #For Deployment on Render

# app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

app.config['SESSION_TYPE'] = 'filesystem'

app.config["WTF_CSRF_CHECK_DEFAULT"] = False
app.config["WTF_CSRF_TIME_LIMIT"] = None
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Important for Google login redirect

Session(app)
csrf = CSRFProtect()
csrf.init_app(app)

# SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_URL = os.environ.get("SUPABASE_URL")

# SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")

@app.route("/")
def home():
    if 'user' in session:
        return redirect("/route_dashboard")
    # print("home session :", session)
    return render_template("index.html", google_client_id=GOOGLE_CLIENT_ID)

@app.route("/auth/callback", methods=["POST"])
def auth_callback():
    # https://console.cloud.google.com/auth/clients?project=codingprofiletracker
    try:
        data = request.get_json()

        credential = data.get("credential")
        if not credential:
            return jsonify({"success": False, "message": "Missing credential"}), 400

        auth_response = supabase.auth.sign_in_with_id_token({
            "provider": "google",
            "token": credential,
        })

        user = auth_response.user
        # print(user)
        email = user.email
        name = user.user_metadata.get("full_name")
        picture = user.user_metadata.get("picture") 

        if not email.endswith("@sitare.org"):
            return jsonify({"success": False, "message": "Only sitare.org emails allowed."}), 403

        session["user"] = user.user_metadata
        session["user_id"] = user.id
        session["avatar_url"] = picture

        username = email.split("@")[0]
        session["dashboard"] = "student" if username.startswith("su-2") else "teacher"

        # Extract the year part from the email and calculate class_of
        if username.startswith("su-"):
            try:
                batch_year = int(username[3:5])  # Extract '22' or '23'
                session["class_of"] = 2000 + batch_year + 4  # e.g., 22 -> 2026
            except ValueError:
                session["class_of"] = None
        else:
            session["class_of"] = 0

        # Save to Supabase
        supabase.table("profiles").upsert({
            "id": user.id,
            "email": email,
            "name": name,
            "avatar_url": picture,
            "role": session["dashboard"],
            "class_of": session["class_of"]
        }).execute()

        return jsonify({"success": True})

    except Exception as e:
        print("Exception:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

# This is a route decorator in Flask. It tells Flask to call the route_dashboard() function,
# whenever a client accesses the URL /route_dashboard.
@app.route("/route_dashboard")
def route_dashboard():
    if "user" not in session:
        return redirect("/")
    # print(session)
    # <FileSystemSession {'_permanent': True, 'csrf_token': 'adbcf557387d815b933a1e32', 'user': {'avatar_url': 'https://lh3.googleusercontent.com/a/ACg8ocJrA3rD6mzcfhDPYE4gnA9uP0o=s96-c', 'custom_claims': {'hd': 'sitare.org'}, 'email': 'su-22010@sitare.org', 'email_verified': True, 'full_name': 'Nagmani kumar', 'iss': 'https://accounts.google.com', 'name': 'Nagmani kumar', 'phone_verified': False, 'picture': 'https://lh3.googleusercontent.com/a/ACg8ocJrA3rD6mzcfhD', 'provider_id': '10310975544785249', 'sub': '10310985544249217'}, 'dashboard': 'student'}>
    dashboard = session.get("dashboard")
    if dashboard == "student":
        return redirect("/student/dashboard")
    elif dashboard == "teacher":
        return redirect("/teacher/dashboard")
    else:
        return redirect("/")


# ------------------- Student Section -------------------


@app.route("/student/dashboard")
def student_dashboard():
    if 'user' in session:
        user = session['user']
        user_id = session["user_id"]
        
        # Fetch the current student data
        response = supabase.table("profiles").select("*").eq('id', user_id).execute()
        if response.data:
            user = response.data[0]
            leetcode_data1 = {}

            try:
                # Get Leetcode data for current student
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
                        'ranking': 'Add Leetcode Profile Link in Edit Profile Section',
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

            # Fetch all students' LeetCode data for university rank calculation
            all_students = supabase.table("profiles").select("*").execute().data
            student_ranks = []

            for student in all_students:
                leetcode_url = student.get('leetcode')
                if leetcode_url:
                    username = leetcode_url.rstrip('/').split("/")[-1]
                    leetcode_data = get_leetcode_data(username)
                    if leetcode_data:
                        student_ranks.append({
                            'id': student['id'],
                            'name': student['name'],
                            'classOf': student['classOf'],
                            'ranking': leetcode_data['ranking'],
                            'totalSolved': leetcode_data['totalSolved']
                        })

            # Sort students by Leetcode ranking (ascending, best rank first)
            student_ranks.sort(key=lambda x: x['ranking'])

            # Assign university ranks
            for idx, student in enumerate(student_ranks):
                student['university_rank'] = idx + 1

            # Find the logged-in user's rank
            user_rank = next((student['university_rank'] for student in student_ranks if student['id'] == user_id), 'N/A')

            # Get top 10 students
            top_10_students = student_ranks[:10]

            # Find University topper (top student)
            university_topper = student_ranks[0] if student_ranks else None

            return render_template('student/dashboard.html', 
                                   user=user, 
                                   leetcode_data1=leetcode_data1,
                                   user_rank=user_rank,  # Pass user's rank to template
                                   university_topper=university_topper,
                                   top_10_students=top_10_students)

    flash('Please log in to access the dashboard.', 'warning')
    return redirect(url_for('home'))



@app.route('/student/assignments/')
def student_assignments():
    if 'user_id' in session:
        user_id = session['user_id']

        response = supabase.from_('profiles').select('*').eq('id', user_id).execute()
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

            status_map = {item['assignment_id']: item['status'] for item in completed_assignments}

            for assignment in assignments:
                assignment['status'] = status_map.get(assignment['id'], 'pending')

                # Optional: If assignment_questions is a related table
                questions = supabase.from_('assignment_questions') \
                    .select('question_number') \
                    .eq('assignment_id', assignment['id']) \
                    .execute().data

                assignment['assignment_questions'] = questions

            return render_template('student/assignments.html', user=user, assignments=assignments)

    flash('Please log in to access the dashboard.', 'warning')
    return redirect(url_for('home'))

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

@app.route("/student/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "user" not in session:
        return redirect("/")

    user_id = session["user_id"]
    session_user = session["user"]  # From Google auth callback

    if request.method == "POST":
        leetcode = request.form["leetcode"]
        github = request.form["github"]
        linkedin = request.form["linkedin"]
        whatsapp = request.form["whatsapp"]

        # Fetch existing user to get email and role
        response = supabase.table("profiles").select("email, role").eq("id", user_id).execute()
        if not response.data:
            flash("User profile not found.", "danger")
            return redirect("/route_dashboard")

        email = response.data[0]["email"]
        role = response.data[0]["role"]

        # Upsert with all required fields
        supabase.table("profiles").upsert({
            "id": user_id,
            "email": email,
            "role": role,
            "name": session_user.get("full_name", ""),
            "leetcode": leetcode,
            "github": github,
            "linkedin": linkedin,
            "whatsapp": whatsapp
        }).execute()

        flash("Profile updated successfully.", "success")
        return redirect("/route_dashboard")

    # For GET, fetch current profile data
    response = supabase.table("profiles").select("*").eq("id", user_id).execute()
    profile = response.data[0] if response.data else {}
    return render_template("student/edit_profile.html", profile=profile, user=session_user)


# ------------------- Teacher Section -------------------


def get_leetcode_data(username):
    try:
        response = requests.get(f"https://leetcode-stats-api.herokuapp.com/{username}")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching data for {username}: {e}")
    return None

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if "user" not in session:
        return redirect("/")

    user = session['user']
    all_students = supabase.from_('profiles').select('*').eq('role', 'student').execute().data

    class_wise_students = {}
    class_wise_toppers = {}
    overall_topper = None
    highest_total = -1

    problem_bins = Counter()
    weighted_scores = []
    leetcode_metrics = []

    for student in all_students:
        class_of = student.get('class_of', 'Unknown')
        if class_of not in class_wise_students:
            class_wise_students[class_of] = []

        url = student.get('leetcode')
        leetcode_data = {}
        totalSolved = 0
        weighted_score = 0

        if url:
            username = url.rstrip('/').split("/")[-1]
            data = get_leetcode_data(username)
            if data:
                leetcode_data = data
                totalSolved = data.get('totalSolved', 0)

                weighted_score = (
                    data.get('easySolved', 0) * 1 +
                    data.get('mediumSolved', 0) * 3 +
                    data.get('hardSolved', 0) * 5
                )

                # Binning
                if totalSolved <= 100:
                    problem_bins['0-100'] += 1
                elif totalSolved <= 200:
                    problem_bins['101-200'] += 1
                elif totalSolved <= 300:
                    problem_bins['201-300'] += 1
                elif totalSolved <= 500:
                    problem_bins['301-500'] += 1
                else:
                    problem_bins['501+'] += 1

                weighted_scores.append(weighted_score)

        student_info = {
            'name': student['name'],
            'class_of': class_of,
            'totalSolved': totalSolved,
            'weighted_score': weighted_score,
        }

        class_wise_students[class_of].append(student_info)

        if class_of not in class_wise_toppers or totalSolved > class_wise_toppers[class_of]['totalSolved']:
            class_wise_toppers[class_of] = student_info

        if totalSolved > highest_total:
            highest_total = totalSolved
            overall_topper = student_info

        leetcode_data['name'] = student['name']
        leetcode_metrics.append(leetcode_data)

        # Filter out invalid entries (e.g. students with 0 problems)
        valid_metrics = [m for m in leetcode_metrics if m['totalSolved'] > 0]

        summary_stats = {}
        highlights = {}

        # Define the metrics you want to show
        metric_keys = ['totalSolved', 'easySolved', 'mediumSolved', 'hardSolved']

        for key in metric_keys:
            values = [(m['name'], m[key]) for m in valid_metrics]
            scores = [v[1] for v in values]

            if not scores:
                continue

            mean = round(statistics.mean(scores), 1)
            median = round(statistics.median(scores), 1)

            sorted_by_score = sorted(values, key=lambda x: x[1], reverse=True)
            top_3 = sorted_by_score[:3]
            bottom_3 = sorted_by_score[-3:]

            top_10_count = max(1, len(scores) // 10)
            bottom_10_count = max(1, len(scores) // 10)

            top_10_avg = round(statistics.mean([v[1] for v in sorted_by_score[:top_10_count]]), 1)
            bottom_10_avg = round(statistics.mean([v[1] for v in sorted_by_score[-bottom_10_count:]]), 1)

            summary_stats[key] = {
                'mean': mean,
                'median': median,
            }

            highlights[key] = {
                'top_3': top_3,
                'bottom_3': bottom_3,
                'top_10_percent_avg': top_10_avg,
                'bottom_10_percent_avg': bottom_10_avg
            }

    return render_template(
        'teacher/dashboard.html',
        user=user,
        summary_stats=summary_stats,
        highlights=highlights,
        metrics=leetcode_metrics,
        class_wise_students=class_wise_students,
        class_wise_toppers=class_wise_toppers,
        overall_topper=overall_topper,
        problem_bins=dict(problem_bins),
        weighted_scores=weighted_scores
    )

@app.route('/teacher/students')
def teacher_students():
    if "user" not in session:
        return redirect("/")
    if 'user_id' in session and session.get('dashboard') == 'teacher':
        students = supabase.from_('profiles').select('*').eq('role', 'student').execute().data

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
    return redirect(url_for('home'))

@app.route('/teacher/assignments')
def assignments_page():
    if "user" not in session:
        return redirect("/")
    user = session['user']
    if 'user_id' in session and session.get('dashboard') == 'teacher':
        # Get all students
        total_students = supabase.from_('profiles').select('*').eq('role', 'student').execute().data

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

        return render_template('teacher/assignments.html', user=user, assignments=assignments)
    
    flash('Access denied.', 'danger')
    return redirect(url_for('home'))


@app.route('/teacher/create_assignment', methods=['POST'])
def create_assignment():
    if 'user_id' in session and session.get('dashboard') == 'teacher':
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
    if 'user_id' in session and session.get('dashboard') == 'teacher':
        # Delete assignment and related data
        supabase.from_('assignments').delete().eq('id', assignment_id).execute()
        supabase.from_('assignment_questions').delete().eq('assignment_id', assignment_id).execute()
        flash('Assignment deleted!', 'success')
        return '', 204  # No content

    flash('Failed to delete assignment.', 'danger')
    return '', 400

@app.route('/teacher/smarttable')
def teacher_smarttable():
    if 'user_id' in session and session.get('dashboard') == 'teacher':
        # Fetch all students
        students = supabase.from_('profiles').select('id, name, email, leetcode').eq('role', 'student').execute().data

        # Fetch LeetCode details for each student
        student_data = []
        for student in students:
            leetcode_data = {}
            try:
                url = student.get('leetcode')
                if url:
                    username = url.rstrip('/').split("/")[-1]
                    leetcode_data = get_leetcode_data(username) or {}
            except Exception as e:
                print(f"Error fetching LeetCode data for {student['name']}: {e}")

            student_data.append({
                'id': student['id'],
                'name': student['name'],
                'email': student['email'],
                'totalSolved': leetcode_data.get('totalSolved', 0),
                'acceptanceRate': leetcode_data.get('acceptanceRate', 0),
                'easySolved': leetcode_data.get('easySolved', 0),
                'mediumSolved': leetcode_data.get('mediumSolved', 0),
                'hardSolved': leetcode_data.get('hardSolved', 0),
                'totalQuestions': leetcode_data.get('totalQuestions', 0),
            })
        
        # Calculate averages
        total_students = len(student_data)
        if total_students > 0:
            avg_total_solved = sum(s['totalSolved'] for s in student_data) / total_students
            avg_acceptance_rate = sum(s['acceptanceRate'] for s in student_data) / total_students
            avg_easy = sum(s['easySolved'] for s in student_data) / total_students
            avg_medium = sum(s['mediumSolved'] for s in student_data) / total_students
            avg_hard = sum(s['hardSolved'] for s in student_data) / total_students
        else:
            avg_total_solved = avg_acceptance_rate = avg_easy = avg_medium = avg_hard = 0

        return render_template('teacher/smarttable.html',
                            students=student_data,
                            avg_total_solved=avg_total_solved,
                            avg_acceptance_rate=avg_acceptance_rate,
                            avg_easy=avg_easy,
                            avg_medium=avg_medium,
                            total_students =total_students ,
                            avg_hard=avg_hard)
    return redirect(url_for('home'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)