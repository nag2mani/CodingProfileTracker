import os
import uuid
from flask_wtf import CSRFProtect
from flask_session import Session
from datetime import datetime
from supabase import create_client, Client
from flask import Flask, request, redirect, url_for, session, render_template, flash, jsonify
from leetcode_api import get_leetcode_data
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SESSION_TYPE'] = 'filesystem'

app.config["WTF_CSRF_CHECK_DEFAULT"] = False
app.config["WTF_CSRF_TIME_LIMIT"] = None
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Important for Google login redirect

Session(app)
csrf = CSRFProtect()
csrf.init_app(app)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

@app.route("/")
def home():
    if 'user' in session:
        return redirect("/route_dashboard")
    # print("home session :", session)
    return render_template("index.html", google_client_id=GOOGLE_CLIENT_ID)

@app.route("/auth/callback", methods=["POST"])
def auth_callback():
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

        if not email.endswith("@sitare.org"):
            return jsonify({"success": False, "message": "Only sitare.org emails allowed."}), 403

        session["user"] = user.user_metadata
        session["user_id"] = user.id

        username = email.split("@")[0]
        session["dashboard"] = "student" if username.startswith("su-2") else "teacher"
        # print(session)

        supabase.table("profiles").upsert({
            "id": user.id,
            "email": email,
            "name" :name
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

# ------------------- Student Dashboard -------------------

@app.route("/student/dashboard")
def student_dashboard():
    if 'user' in session:
        user = session['user']
        email = user['email']
        response = supabase.from_('profiles').select('*').eq('email', email).execute()
        print("response : ", response)
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
    return redirect(url_for('home'))

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

    user_id = session["user"]["sub"]  # unique Google ID
    user = session["user"]
    email = user['email']
    # name = user['full_name']
    if request.method == "POST":
        leetcode = request.form["leetcode"]
        github = request.form["github"]
        linkedin = request.form["linkedin"]
        whatsapp = request.form["whatsapp"]

        supabase.table("profiles").upsert({
            "id": user_id,
            "leetcode": leetcode,
            "github": github,
            "linkedin": linkedin,
            "whatsapp": whatsapp
        }).execute()

        return redirect("/route_dashboard")

    response = supabase.table("profiles").select("*").eq('email', email).execute()
    profile = response.data[0] if response.data else {}

    return render_template("student/edit_profile.html", profile=profile)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)


# @app.route("/dashboard2") #This is Teacher Dashboard.
# def dashboard2():
#     if "user" not in session or session.get("dashboard") != "dashboard2":
#         return redirect("/")
#     user_data = session["user"]
#     return render_template("teacher/dashboard.html", user=user_data)


# # ------------------- Teacher Dashboard -------------------

# @app.route('/teacher/dashboard', methods=['GET'])
# def teacher_dashboard():
#     if 'user_id' not in session or session.get('role') != 'teacher':
#         flash('Access denied.', 'danger')
#         return redirect(url_for('login'))

#     # Fetch all students
#     students = supabase.from_('users').select('*').eq('role', 'student').execute().data

#     # Pagination parameters
#     page = int(request.args.get('page', 1))
#     per_page = 10
#     start = (page - 1) * per_page
#     end = start + per_page

#     # Sorting and filtering parameters
#     sort_by = request.args.get('sort_by', 'totalSolved')
#     search_query = request.args.get('search', '').lower()

#     TOTAL_LEETCODE_USERS = 1000000

#     leetcode_metrics = []
#     for student in students:
#         leetcode_data = {}
#         try:
#             url = student.get('leetcode')
#             if url:
#                 username = url.rstrip('/').split("/")[-1]
#                 leetcode_data = get_leetcode_data(username) or {
#                     'totalSolved': 0,
#                     'totalQuestions': 0,
#                     'easySolved': 0,
#                     'totalEasy': 0,
#                     'mediumSolved': 0,
#                     'totalMedium': 0,
#                     'hardSolved': 0,
#                     'totalHard': 0,
#                     'acceptanceRate': 0,
#                     'ranking': 'N/A',
#                     'contributionPoints': 0,
#                     'submissionCalendar': {}
#                 }
#             else:
#                 leetcode_data = {
#                     'totalSolved': 0,
#                     'totalQuestions': 0,
#                     'easySolved': 0,
#                     'totalEasy': 0,
#                     'mediumSolved': 0,
#                     'totalMedium': 0,
#                     'hardSolved': 0,
#                     'totalHard': 0,
#                     'acceptanceRate': 0,
#                     'ranking': 'N/A',
#                     'contributionPoints': 0,
#                     'submissionCalendar': {}
#                 }

#             total_solved = leetcode_data['totalSolved']
#             easy_pct = (leetcode_data['easySolved'] / leetcode_data['totalEasy'] * 100) if leetcode_data['totalEasy'] > 0 else 0
#             medium_pct = (leetcode_data['mediumSolved'] / leetcode_data['totalMedium'] * 100) if leetcode_data['totalMedium'] > 0 else 0
#             hard_pct = (leetcode_data['hardSolved'] / leetcode_data['totalHard'] * 100) if leetcode_data['totalHard'] > 0 else 0
#             acceptance_rate = leetcode_data['acceptanceRate']
#             completion_rate = (total_solved / leetcode_data['totalQuestions'] * 100) if leetcode_data['totalQuestions'] > 0 else 0
#             weighted_score = (leetcode_data['easySolved'] * 1) + (leetcode_data['mediumSolved'] * 3) + (leetcode_data['hardSolved'] * 5)
#             ranking = leetcode_data['ranking']
#             ranking_pct = (1 - (int(ranking) / TOTAL_LEETCODE_USERS)) * 100 if ranking != 'N/A' and TOTAL_LEETCODE_USERS > 0 else 0
#             contrib_per_problem = (leetcode_data['contributionPoints'] / total_solved) if total_solved > 0 else 0

#             calendar = leetcode_data.get('submissionCalendar', {})
#             if calendar:
#                 timestamps = [int(ts) for ts in calendar.keys()]
#                 if timestamps:
#                     earliest = min(timestamps)
#                     latest = max(timestamps)
#                     total_days = (latest - earliest) // 86400 + 1
#                     active_days = len(calendar)
#                     consistency = (active_days / total_days) * 100 if total_days > 0 else 0
#                 else:
#                     consistency = 0
#             else:
#                 consistency = 0

#             peak_activity = max(calendar.values()) if calendar else 0

#             leetcode_metrics.append({
#                 'name': student['name'],
#                 'totalSolved': total_solved,
#                 'easy_pct': round(easy_pct, 2),
#                 'medium_pct': round(medium_pct, 2),
#                 'hard_pct': round(hard_pct, 2),
#                 'acceptanceRate': acceptance_rate,
#                 'completionRate': round(completion_rate, 2),
#                 'weightedScore': weighted_score,
#                 'ranking_pct': round(ranking_pct, 2) if ranking != 'N/A' else 'N/A',
#                 'contribPerProblem': round(contrib_per_problem, 2),
#                 'consistency': round(consistency, 2),
#                 'peakActivity': peak_activity,
#                 'submissionCalendar': calendar
#             })
#         except Exception as e:
#             print(f"Error fetching LeetCode data for {student['name']}: {e}")
#             leetcode_metrics.append({
#                 'name': student['name'],
#                 'totalSolved': 0,
#                 'easy_pct': 0,
#                 'medium_pct': 0,
#                 'hard_pct': 0,
#                 'acceptanceRate': 0,
#                 'completionRate': 0,
#                 'weightedScore': 0,
#                 'ranking_pct': 'N/A',
#                 'contribPerProblem': 0,
#                 'consistency': 0,
#                 'peakActivity': 0,
#                 'submissionCalendar': {}
#             })

#     # Apply search filter
#     if search_query:
#         leetcode_metrics = [student for student in leetcode_metrics if search_query in student['name'].lower()]

#     # Sort by selected metric
#     sort_key_map = {
#         'totalSolved': 'totalSolved',
#         'easy_pct': 'easy_pct',
#         'medium_pct': 'medium_pct',
#         'hard_pct': 'hard_pct',
#         'acceptanceRate': 'acceptanceRate',
#         'completionRate': 'completionRate',
#         'weightedScore': 'weightedScore',
#         'ranking_pct': 'ranking_pct',
#         'contribPerProblem': 'contribPerProblem',
#         'consistency': 'consistency',
#         'peakActivity': 'peakActivity'
#     }
#     sort_key = sort_key_map.get(sort_by, 'totalSolved')
#     leetcode_metrics.sort(key=lambda x: x[sort_key] if x[sort_key] != 'N/A' else -float('inf'), reverse=True)

#     # Compute Summary Statistics and Highlights
#     metrics_list = [
#         'totalSolved', 'easy_pct', 'medium_pct', 'hard_pct', 'acceptanceRate',
#         'completionRate', 'weightedScore', 'ranking_pct', 'contribPerProblem',
#         'consistency', 'peakActivity'
#     ]
#     summary_stats = {}
#     highlights = {}

#     for metric in metrics_list:
#         values = [student[metric] for student in leetcode_metrics if student[metric] != 'N/A']
#         if not values:
#             summary_stats[metric] = {
#                 'mean': 0,
#                 'median': 0,
#                 'std_dev': 0,
#                 'min': 0,
#                 'max': 0,
#                 'q1': 0,
#                 'q3': 0,
#                 'range': 0
#             }
#             highlights[metric] = {
#                 'top_3': [],
#                 'bottom_3': [],
#                 'top_10_percent_avg': 0,
#                 'bottom_10_percent_avg': 0
#             }
#             continue

#         # Summary Statistics
#         mean = statistics.mean(values)
#         median = statistics.median(values)
#         std_dev = statistics.stdev(values) if len(values) > 1 else 0
#         min_val = min(values)
#         max_val = max(values)
#         q1 = statistics.quantiles(values, n=4)[0]  # 25th percentile
#         q3 = statistics.quantiles(values, n=4)[2]  # 75th percentile
#         range_val = max_val - min_val

#         summary_stats[metric] = {
#             'mean': round(mean, 2),
#             'median': round(median, 2),
#             'std_dev': round(std_dev, 2),
#             'min': round(min_val, 2),
#             'max': round(max_val, 2),
#             'q1': round(q1, 2),
#             'q3': round(q3, 2),
#             'range': round(range_val, 2)
#         }

#         # Highlights
#         sorted_students = sorted(leetcode_metrics, key=lambda x: x[metric] if x[metric] != 'N/A' else -float('inf'), reverse=True)
#         top_3 = [(s['name'], s[metric]) for s in sorted_students[:3] if s[metric] != 'N/A']
#         bottom_3 = [(s['name'], s[metric]) for s in sorted_students[-3:] if s[metric] != 'N/A'][::-1]

#         # Top 10% and Bottom 10%
#         n = len(values)
#         top_10_percent = sorted_students[:max(1, n // 10)]
#         bottom_10_percent = sorted_students[-max(1, n // 10):]
#         top_10_percent_avg = statistics.mean([s[metric] for s in top_10_percent if s[metric] != 'N/A']) if top_10_percent else 0
#         bottom_10_percent_avg = statistics.mean([s[metric] for s in bottom_10_percent if s[metric] != 'N/A']) if bottom_10_percent else 0

#         highlights[metric] = {
#             'top_3': top_3,
#             'bottom_3': bottom_3,
#             'top_10_percent_avg': round(top_10_percent_avg, 2),
#             'bottom_10_percent_avg': round(bottom_10_percent_avg, 2)
#         }

#         # Histogram Data (for distribution)
#         if metric in ['totalSolved', 'weightedScore', 'peakActivity']:
#             bins = 10
#             hist, bin_edges = [], []
#             if values:
#                 min_val, max_val = min(values), max(values)
#                 bin_size = (max_val - min_val) / bins if max_val > min_val else 1
#                 hist = [0] * bins
#                 for val in values:
#                     bin_idx = min(int((val - min_val) / bin_size), bins - 1)
#                     hist[bin_idx] += 1
#                 bin_edges = [min_val + i * bin_size for i in range(bins + 1)]
#             summary_stats[metric]['histogram'] = hist
#             summary_stats[metric]['bin_edges'] = bin_edges

#     # For charts: Show top 10 students (or fewer if filtered)
#     chart_metrics = leetcode_metrics[:10]

#     # For table: Apply pagination
#     total_students = len(leetcode_metrics)
#     table_metrics = leetcode_metrics[start:end]
#     total_pages = (total_students + per_page - 1) // per_page

#     # For detailed graphs: List of all student names
#     all_student_names = [student['name'] for student in students]

#     return render_template('teacher/dashboard.html',
#                          username=session.get('username'),
#                          leetcode_metrics=chart_metrics,
#                          table_metrics=table_metrics,
#                          total_pages=total_pages,
#                          current_page=page,
#                          sort_by=sort_by,
#                          search_query=search_query,
#                          total_students=total_students,
#                          all_student_names=all_student_names,
#                          summary_stats=summary_stats,
#                          highlights=highlights)
#     flash('Access denied.', 'danger')
#     return redirect(url_for('login'))

# @app.route('/teacher/students')
# def teacher_students():
#     if 'user_id' in session and session.get('role') == 'teacher':
#         students = supabase.from_('users').select('*').eq('role', 'student').execute().data

#         # Fetch LeetCode rank for each student
#         for student in students:
#             leetcode_data = {}
#             try:
#                 url = student.get('leetcode')
#                 if url:
#                     username = url.rstrip('/').split("/")[-1]
#                     leetcode_data = get_leetcode_data(username) or {}
#                 student['leetcode_rank'] = leetcode_data.get('ranking', 'N/A')
#             except Exception as e:
#                 student['leetcode_rank'] = 'N/A'
#                 print(f"Error fetching LeetCode data for {student['name']}: {e}")

#         # Sort students by LeetCode rank (convert 'N/A' to large number to push them to the end)
#         students.sort(key=lambda x: int(x['leetcode_rank']) if x['leetcode_rank'] != 'N/A' else float('inf'))

#         return render_template('teacher/students.html', students=students)

#     flash('Access denied.', 'danger')
#     return redirect(url_for('login'))



# # ------------------- Assignments Page -------------------
# @app.route('/teacher/assignments')
# def assignments_page():
#     if 'user_id' in session and session.get('role') == 'teacher':
#         # Get all students
#         total_students = supabase.from_('users').select('*').eq('role', 'student').execute().data
#         total_students_count = len(total_students)

#         # Get assignments created by the teacher
#         assignments = supabase.from_('assignments').select('*').eq('created_by', session['user_id']).execute().data

#         for assignment in assignments:
#             # Count completed assignments
#             completed_count = supabase.from_('student_assignments') \
#                 .select('id') \
#                 .eq('assignment_id', assignment['id']) \
#                 .eq('status', 'completed') \
#                 .execute().data

#             assignment['completed_count'] = len(completed_count)
#             assignment['total_students'] = total_students_count

#             # Get all questions for the assignment
#             questions = supabase.from_('assignment_questions') \
#                 .select('question_number') \
#                 .eq('assignment_id', assignment['id']) \
#                 .execute().data

#             assignment['questions'] = [q['question_number'] for q in questions]

#         return render_template('teacher/assignments.html', assignments=assignments)
    
#     flash('Access denied.', 'danger')
#     return redirect(url_for('login'))


# @app.route('/teacher/create_assignment', methods=['POST'])
# def create_assignment():
#     if 'user_id' in session and session.get('role') == 'teacher':
#         name = request.form.get('name')
#         question_numbers = request.form.get('questions').split(',')
#         deadline = request.form.get('deadline')

#         assignment_id = str(uuid.uuid4())

#         assignment_data = {
#             'id': assignment_id,
#             'name': name,
#             'created_by': session['user_id'],
#             'deadline': deadline,
#             'created_at': datetime.now().isoformat()
#         }

#         supabase.from_('assignments').insert(assignment_data).execute()

#         for q in question_numbers:
#             question_data = {
#                 'id': str(uuid.uuid4()),
#                 'assignment_id': assignment_id,
#                 'question_number': int(q.strip())
#             }
#             supabase.from_('assignment_questions').insert(question_data).execute()

#         flash('Assignment created!', 'success')
#         return redirect(url_for('assignments_page'))  # Redirect to assignments page

#     flash('Failed to create assignment.', 'danger')
#     return redirect(url_for('assignments_page'))


# @app.route('/teacher/delete_assignment/<assignment_id>', methods=['POST'])
# def delete_assignment(assignment_id):
#     if 'user_id' in session and session.get('role') == 'teacher':
#         # Delete assignment and related data
#         supabase.from_('assignments').delete().eq('id', assignment_id).execute()
#         supabase.from_('assignment_questions').delete().eq('assignment_id', assignment_id).execute()
#         flash('Assignment deleted!', 'success')
#         return '', 204  # No content

#     flash('Failed to delete assignment.', 'danger')
#     return '', 400


# @app.route('/teacher/smarttable')
# def teacher_smarttable():
#     if 'user_id' in session and session.get('role') == 'teacher':
#         # Fetch all students
#         students = supabase.from_('users').select('id, name, email, leetcode').eq('role', 'student').execute().data

#         # Fetch LeetCode details for each student
#         student_data = []
#         for student in students:
#             leetcode_data = {}
#             try:
#                 url = student.get('leetcode')
#                 if url:
#                     username = url.rstrip('/').split("/")[-1]
#                     leetcode_data = get_leetcode_data(username) or {}
#             except Exception as e:
#                 print(f"Error fetching LeetCode data for {student['name']}: {e}")

#             student_data.append({
#                 'id': student['id'],
#                 'name': student['name'],
#                 'email': student['email'],
#                 'ranking': leetcode_data.get('ranking', 'N/A'),
#                 'totalSolved': leetcode_data.get('totalSolved', 0),
#                 'acceptanceRate': leetcode_data.get('acceptanceRate', 0),
#                 'easySolved': leetcode_data.get('easySolved', 0),
#                 'mediumSolved': leetcode_data.get('mediumSolved', 0),
#                 'hardSolved': leetcode_data.get('hardSolved', 0),
#                 'totalQuestions': leetcode_data.get('totalQuestions', 0),
#             })


#         return render_template('teacher/smarttable.html', students=student_data)

#     flash('Access denied.', 'danger')
#     return redirect(url_for('login'))