import requests

# def get_leetcode_data(username):
#     url = f"https://leetcode-stats-api.herokuapp.com/{username}"
#     try:
#         response = requests.get(url, timeout=5)
#         print("Status of Response:", response.status_code)
#         if response.status_code == 200:
#             return response.json()
#     except requests.RequestException as e:
#         print("Error fetching LeetCode data:", e)
#     return None

# import requests

def get_leetcode_data(username):
    url = f"https://leetcode-stats-api.herokuapp.com/{username}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()

            # Ensure the returned data matches the template structure
            return {
                'ranking': data.get('ranking', 'N/A'),
                'totalSolved': data.get('totalSolved', 0),
                'totalQuestions': data.get('totalQuestions', 0),
                'easySolved': data.get('easySolved', 0),
                'totalEasy': data.get('totalEasy', 0),
                'mediumSolved': data.get('mediumSolved', 0),
                'totalMedium': data.get('totalMedium', 0),
                'hardSolved': data.get('hardSolved', 0),
                'totalHard': data.get('totalHard', 0),
                'acceptanceRate': data.get('acceptanceRate', 0),
                'contributionPoints': data.get('contributionPoints', 0),
                'reputation': data.get('reputation', 0),
            }
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


