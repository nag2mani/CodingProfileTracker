"""
Chatbot module for the Coding Profile Tracker application.

This module provides an AI-powered analytics chatbot that answers natural language
queries about student coding statistics. It uses Google Gemini to interpret questions,
analyze dummy/demo student data (LeetCode-style metrics), and returns HTML responses
with optional matplotlib/seaborn visualizations. Intended for demo or standalone
chatbot usage (e.g., on a separate port). The main app may integrate similar
chatbot functionality via app.py.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from flask import Flask, render_template, request, jsonify, url_for
import random
from datetime import datetime, timedelta
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
import base64
import os
import google.generativeai as genai
import re
from enum import Enum

# ---------------------------------------------------------------------------
# App and API configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Google Gemini API key for LLM-powered query handling
gemini_api_key = os.environ.get("GOOGLE_API_KEY")

if not gemini_api_key:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

# Configure Gemini
genai.configure(api_key=gemini_api_key)

# Create reusable model client
client = genai.GenerativeModel("gemini-1.5-flash")

# Use non-interactive backend for matplotlib (required when no display is available)
plt.switch_backend('Agg')

# Plot styling
sns.set_style("whitegrid")
plt.style.use('seaborn')

# Directory for saving generated chart images (relative to cwd)
STATIC_FOLDER = os.path.join(os.getcwd(), '../static')
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)


# ---------------------------------------------------------------------------
# Data generation and in-memory dataset
# ---------------------------------------------------------------------------

def generate_dummy_data():
    """
    Build an in-memory dataset of fake student LeetCode-style statistics.

    Creates a dictionary keyed by student name, with values containing
    totalSolved, easy/medium/hard counts, acceptance rate, and a 30-day
    submission calendar. Used for demo/dashboard when real LeetCode API
    data is not wired in.

    Returns:
        dict: Mapping of student name -> dict of stats (totalSolved, easySolved,
              mediumSolved, hardSolved, acceptanceRate, submissionCalendar, etc.).
    """
    students = {}
    names = ["Alice", "Bob", "Charlie", "David", "Eva", "Frank", "Grace", "Henry", "Ivy", "Jack"]

    for name in names:
        # Simulate last 30 days of submission counts per day
        submission_calendar = {}
        current_date = datetime.now()
        for i in range(30):  # Last 30 days
            date = int((current_date - timedelta(days=i)).timestamp())
            submission_calendar[str(date)] = random.randint(0, 15)

        students[name] = {
            "status": "success",
            "message": "retrieved",
            "totalSolved": random.randint(100, 300),
            "totalQuestions": 3476,
            "easySolved": random.randint(40, 100),
            "totalEasy": 863,
            "mediumSolved": random.randint(30, 150),
            "totalMedium": 1807,
            "hardSolved": random.randint(5, 30),
            "totalHard": 806,
            "acceptanceRate": round(random.uniform(50, 70), 2),
            "submissionCalendar": submission_calendar
        }

    return students


# Global in-memory dataset used by the chatbot for analysis and by Gemini prompts
STUDENTS_DATA = generate_dummy_data()


# ---------------------------------------------------------------------------
# Analysis helpers: build DataFrames from STUDENTS_DATA for charts/stats
# ---------------------------------------------------------------------------

def analyze_total_problems(students_data):
    """
    Compute total problems solved per student and return a sorted DataFrame.

    Args:
        students_data (dict): Map of student name -> stats dict (must have
                              'totalSolved' key).

    Returns:
        pd.DataFrame: Two columns: 'Student', 'Total Solved', sorted by
                      'Total Solved' descending.
    """
    df = pd.DataFrame({
        'Student': list(students_data.keys()),
        'Total Solved': [data['totalSolved'] for data in students_data.values()]
    })
    return df.sort_values('Total Solved', ascending=False)


def analyze_difficulty_distribution(students_data):
    """
    Build a DataFrame of easy/medium/hard solved counts per student.

    Args:
        students_data (dict): Map of student name -> stats with 'easySolved',
                             'mediumSolved', 'hardSolved'.

    Returns:
        pd.DataFrame: Columns 'Student', 'Easy', 'Medium', 'Hard'.
    """
    data = []
    for name, stats in students_data.items():
        data.append({
            'Student': name,
            'Easy': stats['easySolved'],
            'Medium': stats['mediumSolved'],
            'Hard': stats['hardSolved']
        })
    return pd.DataFrame(data)


def analyze_activity_trends(student_name, students_data):
    """
    Extract submission calendar for one student as a time-series DataFrame.

    Args:
        student_name (str): Key in students_data.
        students_data (dict): Map of student name -> stats; each stats dict
                              must have 'submissionCalendar' (timestamp -> count).

    Returns:
        pd.DataFrame | None: Columns 'Date', 'Submissions', sorted by Date;
                              None if student_name not in students_data.
    """
    if student_name not in students_data:
        return None

    calendar = students_data[student_name]['submissionCalendar']
    dates = [datetime.fromtimestamp(int(ts)) for ts in calendar.keys()]
    submissions = list(calendar.values())

    return pd.DataFrame({
        'Date': dates,
        'Submissions': submissions
    }).sort_values('Date')


def analyze_acceptance_rate(students_data):
    """
    Build a DataFrame of acceptance rate per student, sorted by rate descending.

    Args:
        students_data (dict): Map of student name -> stats with 'acceptanceRate'.

    Returns:
        pd.DataFrame: Columns 'Student', 'Acceptance Rate'.
    """
    df = pd.DataFrame({
        'Student': list(students_data.keys()),
        'Acceptance Rate': [data['acceptanceRate'] for data in students_data.values()]
    })
    return df.sort_values('Acceptance Rate', ascending=False)


def analyze_peer_ranking(students_data):
    """
    Compute a weighted score per student (easy*1 + medium*2 + hard*3) and rank.

    Args:
        students_data (dict): Map of student name -> stats with easySolved,
                             mediumSolved, hardSolved.

    Returns:
        pd.DataFrame: Columns 'Student', 'Score', sorted by Score descending.
    """
    rankings = []
    for name, data in students_data.items():
        total_score = (data['easySolved'] * 1 +
                      data['mediumSolved'] * 2 +
                      data['hardSolved'] * 3)
        rankings.append({
            'Student': name,
            'Score': total_score
        })
    return pd.DataFrame(rankings).sort_values('Score', ascending=False)


def generate_visualization(analysis_type, data, title):
    """
    Create a chart from a DataFrame and return it as a base64-encoded PNG string.

    Supports 'bar' (single series), 'stacked' (stacked bar by Student), and
    'line' (Date vs Submissions) plot types. Figure is saved to a buffer,
    encoded, then closed to avoid memory leaks.

    Args:
        analysis_type (str): One of 'bar', 'stacked', 'line'.
        data (pd.DataFrame): Data to plot; expected columns vary by type
                             (e.g. Student + value, or Date + Submissions).
        title (str): Chart title.

    Returns:
        str | None: Base64-encoded PNG string, or None on error.
    """
    fig = plt.figure(figsize=(10, 6))
    try:
        if analysis_type == 'bar':
            ax = sns.barplot(data=data, x=data.columns[0], y=data.columns[1])
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        elif analysis_type == 'stacked':
            data.set_index('Student').plot(kind='bar', stacked=True, ax=plt.gca())
            plt.gca().set_xticklabels(plt.gca().get_xticklabels(), rotation=45, ha='right')
        elif analysis_type == 'line':
            plt.plot(data['Date'], data['Submissions'])
            plt.gcf().autofmt_xdate()

        plt.title(title)
        plt.tight_layout()

        # Save figure to in-memory buffer and encode as base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode()

        plt.close(fig)
        buf.close()

        return image_base64
    except Exception as e:
        plt.close(fig)
        print(f"Error generating visualization: {e}")
        return None


# ---------------------------------------------------------------------------
# Response type enum for structured model output
# ---------------------------------------------------------------------------

class ResponseType(Enum):
    """Enum for the two parts of the model response: HTML text and optional Python code."""
    HTML_RESPONSE = "html_response"
    CODE_RESPONSE = "code_response"


# ---------------------------------------------------------------------------
# Query processing and Gemini integration
# ---------------------------------------------------------------------------

def get_content_from_model(question, data):
    """
    Send the user question and current student data to Gemini; return HTML and optional code.

    Prompts the model to produce (1) an HTML snippet (title + paragraph, and optional
    img tag for static/generated_image.png) and (2) optional Python code that generates
    a chart and saves it as generated_image.png in the static folder. The response
    text is split on ```python to separate HTML from code.

    Args:
        question (str): Natural language query from the user.
        data (dict): Student stats dictionary (e.g. STUDENTS_DATA) for context.

    Returns:
        dict: Keys from ResponseType (HTML_RESPONSE, CODE_RESPONSE). Values are
              the HTML string and/or code string. On exception, may return a
              single HTML_RESPONSE with an error message.
    """
    prompt = (
        f"""You are tasked with generating two types of responses based on a user query and input data: **HTML** and **Python code**.

    ### **1. HTML Response**:
    - The response should be in HTML format. It should include an <h1> title for the analysis result, followed by a <p> tag displaying the text response.
    - If there is a chart image generated, include it as an <img> tag with the value as `static/generated_image.png`. Ensure the image is correctly saved, not empty or blank.

    ### **2. Python Code for Visualization**:
    - Generate Python code that uses `matplotlib` (or any other appropriate library like `seaborn` or `plotly`) to visualize the data in a meaningful way.
    - The code should plot visualizations such as bar charts comparing categories, percentage distributions, or trends over time.
    - Ensure that you are handling cases where the data might be empty or invalid. The chart should only be generated if valid data is provided.
    - The image name should always be `"generated_image.png"`, and it should be saved in the `static` folder.
    - The path used in the HTML will be `static/generated_image.png`.
    - Include print statements in the code to log the data processing steps, such as:
        - Printing the data used for plotting.
        - Indicating when the plot is being created.
        - Confirming when the image is saved and where.
    - Ensure that after plotting, the figure is saved using `plt.savefig()` and that `plt.close()` is called after saving to avoid memory issues or blank images.

    ### **User's Question**:
    - {question}

    ### **Input Data**:
    - {data}
    """
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    )

    try:
        response_data_model = response.candidates[0].content.parts[0].text

        # Split on ```python to separate HTML (before) from code block (after)
        sections = response_data_model.split("```python")
        html_response = sections[0].strip("`html")
        code_response = sections[1].strip("`") if len(sections) > 1 else None

        if html_response and code_response:
            return {
                ResponseType.HTML_RESPONSE: html_response,
                ResponseType.CODE_RESPONSE: code_response
            }
        elif html_response:
            return {
                ResponseType.HTML_RESPONSE: html_response
            }
        elif code_response:
            return {
                ResponseType.CODE_RESPONSE: code_response
            }

    except Exception as e:
        return {
            ResponseType.HTML_RESPONSE: f"<html><body><h1>Error: {str(e)}</h1></body></html>"
        }


def process_query(query):
    """
    Handle a single user query: get model response, run optional code, merge HTML with image.

    Calls get_content_from_model with the global STUDENTS_DATA, then normalizes
    the HTML (strip extra newlines). If both HTML and code are present, executes
    the code via run_code_and_generate_image to produce the chart, then
    injects the resulting image URL into the HTML in place of the placeholder
    "static/generated_image.png". Returns HTML only, or an error HTML string.

    Args:
        query (str): User's natural language question.

    Returns:
        str: HTML string to render in the frontend (with optional embedded image),
             or an error message wrapped in HTML.
    """
    global STUDENTS_DATA  # Access the global variable

    response_data = get_content_from_model(query, STUDENTS_DATA)

    # Normalize HTML: collapse newlines and strip surrounding whitespace
    if ResponseType.HTML_RESPONSE in response_data:
        html_response = response_data[ResponseType.HTML_RESPONSE]
        html_response = re.sub(r'\n+', ' ', html_response).strip()
    else:
        html_response = ''

    if ResponseType.CODE_RESPONSE in response_data:
        code_response = response_data[ResponseType.CODE_RESPONSE]
    else:
        code_response = None

    # If both HTML and code are present, run code to generate image and embed URL in HTML
    if html_response and code_response:
        image_url = run_code_and_generate_image(code_response)
        html_response_with_image = html_response.replace('"static/generated_image.png"', image_url)
        return html_response_with_image

    elif html_response:
        return html_response
    elif code_response:
        return f"<html><body><h1>Code generated, but no HTML response available.{response_data}</h1></body></html>"

    return "<html><body><h1>Error: Unable to process the query.</h1></body></html>"


def run_code_and_generate_image(code_response):
    """
    Execute the model-generated Python code in a restricted context and return image URL.

    The code is run with 'plt', 'os', 'data' (STUDENTS_DATA), and a path/url_for
    available in its namespace. It is expected to use matplotlib/seaborn to create
    a figure and save it to the static folder as generated_image.png. This function
    then returns the Flask url_for the static file so the frontend can display it.

    Args:
        code_response (str): Python code string (typically from Gemini) that produces
                             and saves a chart.

    Returns:
        str: Flask url_for('static', filename='generated_image.png'), or an error
             message string if execution fails.
    """
    try:
        image_path = os.path.join(os.getcwd(), 'static', 'generated_image.png')

        exec_context = {
            'plt': plt,
            'os': os,
            'data': STUDENTS_DATA,
            'url_for': image_path
        }
        exec(code_response, exec_context)

        plt.switch_backend('Agg')

        return url_for('static', filename='generated_image.png')

    except Exception as e:
        return f"Error generating the image: {str(e)}"


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@app.route('/')
def home():
    """
    Serve the main chatbot page.

    Returns:
        Rendered template 'index.html' (chatbot UI).
    """
    return render_template('index.html')


@app.route('/query', methods=['POST'])
def handle_query():
    """
    Accept a JSON body with 'query', run process_query, and return the result as JSON.

    Expects request.json['query'] to be the user's natural language question.
    Returns a JSON object with the HTML (or error) string from process_query.

    Returns:
        JSON response with the processed HTML string.
    """
    query = request.json.get('query', '')
    return jsonify(process_query(query))


# ---------------------------------------------------------------------------
# Entry point for running this module as a standalone app (e.g. port 4000)
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, port=4000)
