from flask import Flask, render_template, request, jsonify, url_for
import random
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
import base64
import os
from google import genai
import re
import matplotlib.pyplot as plt
from enum import Enum

app = Flask(__name__)

gemini_api_key = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=gemini_api_key)

# Set Matplotlib to use a non-interactive backend
plt.switch_backend('Agg')

# Configure Seaborn style
sns.set_style("whitegrid")
plt.style.use('seaborn')

STATIC_FOLDER = os.path.join(os.getcwd(), '../static')
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

# Generate dummy data
def generate_dummy_data():
    students = {}
    names = ["Alice", "Bob", "Charlie", "David", "Eva", "Frank", "Grace", "Henry", "Ivy", "Jack"]
    
    for name in names:
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

# Initialize the global STUDENTS_DATA
STUDENTS_DATA = generate_dummy_data()

def analyze_total_problems(students_data):
    df = pd.DataFrame({
        'Student': list(students_data.keys()),
        'Total Solved': [data['totalSolved'] for data in students_data.values()]
    })
    return df.sort_values('Total Solved', ascending=False)

def analyze_difficulty_distribution(students_data):
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
    df = pd.DataFrame({
        'Student': list(students_data.keys()),
        'Acceptance Rate': [data['acceptanceRate'] for data in students_data.values()]
    })
    return df.sort_values('Acceptance Rate', ascending=False)

def analyze_peer_ranking(students_data):
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

def process_query(query):
    global STUDENTS_DATA  # Access the global variable

    # Get the response data from the model
    response_data = get_content_from_model(query, STUDENTS_DATA)

    # Clean up the HTML response by removing unnecessary newlines and extra spaces
    if ResponseType.HTML_RESPONSE in response_data:
        html_response = response_data[ResponseType.HTML_RESPONSE]
        html_response = re.sub(r'\n+', ' ', html_response).strip()  # Remove extra newlines
    else:
        html_response = ''

    if ResponseType.CODE_RESPONSE in response_data:
        code_response = response_data[ResponseType.CODE_RESPONSE]
    else:
        code_response = None

    # If both HTML and code responses exist
    if html_response and code_response:
        image_url = run_code_and_generate_image(code_response)
        html_response_with_image = html_response.replace('"static/generated_image.png"', image_url)
        return html_response_with_image

    # Handle only HTML or code response separately
    elif html_response:
        return html_response
    elif code_response:
        return f"<html><body><h1>Code generated, but no HTML response available.{response_data}</h1></body></html>"

    return "<html><body><h1>Error: Unable to process the query.</h1></body></html>"


class ResponseType(Enum):
    HTML_RESPONSE = "html_response"
    CODE_RESPONSE = "code_response"

def get_content_from_model(question, data):
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


    # Generate response from the model (assuming model.generate_content is defined)
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    )

    try:
        # Get the response text directly from the 'text' attribute of the first part
        response_data_model = response.candidates[0].content.parts[0].text
        
        # Split the content to get the HTML response and code
        sections = response_data_model.split("```python")
        html_response = sections[0].strip("`html")
        code_response = sections[1].strip("`") if len(sections) > 1 else None
        # print(html_response, "-----------------\n", code_response)
        # Return the appropriate response based on enum
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

# Function to execute the code and generate the graph
def run_code_and_generate_image(code_response):
    try:
        # Run the Python code dynamically using exec (be cautious when using exec in production environments)
        image_path = os.path.join(os.getcwd(), 'static', 'generated_image.png')

        exec_context = {
            'plt': plt,               # Include matplotlib for plotting
            'os': os,                 # Include os for file system operations
            'data': STUDENTS_DATA,             # Inject the data variable from the outside
            'url_for': image_path        # Ensure url_for is available for generating image URLs
        }
        exec(code_response, exec_context)
        
        # Define the image file path
        plt.switch_backend('Agg')

        
        # Return the URL for the frontend to use (Flask will serve static files from the 'static' folder)
        return url_for('static', filename='generated_image.png')
    
    except Exception as e:
        return f"Error generating the image: {str(e)}"
 
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def handle_query():
    query = request.json.get('query', '')
    return jsonify(process_query(query))

if __name__ == '__main__':
    app.run(debug=True, port=4000)