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

