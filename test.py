import requests
from bs4 import BeautifulSoup

def get_leetcode_data(username):
    url = f"https://leetcode.com/{username}/"
    response = requests.get(url)
    
    if response.status_code != 200:
        return None  # Profile not found

    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        # Fetching total problems solved
        total_solved = soup.find('span', class_="text-[24px]").text.strip()
        
        # Fetching ranking
        rank_div = soup.find('div', class_="text-label-1 dark:text-dark-label-1 flex items-center text-base font-medium")
        ranking = rank_div.text.strip() if rank_div else "N/A"
        
        return {
            "total_solved": total_solved,
            "ranking": ranking
        }
    except AttributeError:
        return None

print(get_leetcode_data("nag2mani"))