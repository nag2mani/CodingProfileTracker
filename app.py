from flask import Flask, request, render_template, redirect, url_for, jsonify
import requests
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost:5432/leetcode_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    leetcode_username = db.Column(db.String(100), unique=True, nullable=False)
    easy_solved = db.Column(db.Integer, default=0)
    medium_solved = db.Column(db.Integer, default=0)
    hard_solved = db.Column(db.Integer, default=0)
    ranking = db.Column(db.Integer, default=0)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['leetcode_username']
        new_student = Student(name=name, leetcode_username=username)
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('index'))
    
    students = Student.query.all()
    return render_template('index.html', students=students)

@app.route('/fetch_data/<username>', methods=['GET'])
def fetch_data(username):
    url = f"https://leetcode-stats-api.herokuapp.com/{username}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        student = Student.query.filter_by(leetcode_username=username).first()
        if student:
            student.easy_solved = data['easySolved']
            student.medium_solved = data['mediumSolved']
            student.hard_solved = data['hardSolved']
            student.ranking = data['ranking']
            db.session.commit()
        return redirect(url_for('index'))
    return jsonify({'error': 'Invalid username'}), 404

if __name__ == '__main__':
    app.run(debug=True)
