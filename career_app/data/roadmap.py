PROJECT_NAMES = {
    1: "VFX Production Intelligence Dashboard",
    2: "Retail Operations Performance Dashboard",
    3: "Movie Industry Financial Analytics",
}

PROJECT_DIRS = {
    1: "project-01-vfx-production-intelligence",
    2: "project-02-retail-operations",
    3: "project-03-movie-industry-financial-analytics",
}

PROJECT_STAGES = [
    "Overview", "Tasks", "Dataset", "SQL", "Python", "Power BI",
    "GitHub", "README", "Resume Bullet", "Presentation", "Reflection",
]

WEEKLY_GUIDANCE = {
    1: ("Build Momentum", "Continue Course 5", "Introduction to SQL → Intermediate SQL",
        ["Histogram of Tweets", "Data Science Skills"],
        "Define the VFX project charter, business questions, dataset, and star schema."),
    2: ("Working With Data", "Finish Course 5 and begin Course 6",
        "Intermediate SQL → Joining Data in SQL",
        ["Pharmacy Analytics Part 1", "Signup Activation Rate"],
        "Generate the VFX dataset and create the SQL schema."),
    3: ("Analytical SQL", "Continue Course 6",
        "Joining Data in SQL → Data Manipulation in SQL",
        ["User's Third Transaction", "Second Highest Salary"],
        "Complete the main SQL analysis for Project 1."),
    4: ("First Dashboard", "Progress through Course 6", "Introduction to Power BI",
        ["Top Three Salaries", "Tweets' Rolling Averages"],
        "Build the first Power BI dashboard prototype."),
    5: ("Dashboard Development", "Begin Course 7", "Power BI fundamentals",
        ["Odd and Even Measurements"], "Build executive and workload pages."),
    6: ("Publish Project 1", "Continue Course 7", "Advanced Power BI",
        ["User Shopping Sprees"], "Complete and publish Project 1."),
    7: ("Begin Retail Analytics", "Begin Course 8", "Python and Pandas",
        ["Supercloud Customer"], "Define and prepare Project 2."),
    8: ("Retail Analysis", "Continue Course 8", "Data cleaning and EDA",
        ["Second Day Confirmation"], "Build Project 2 analysis and prototype."),
    9: ("Publish Retail Project", "Finish Course 8", "Statistics fundamentals",
        ["Medium SQL review"], "Complete and publish Project 2."),
    10: ("Begin Movie Analytics", "Begin Course 9 or capstone", "Data storytelling",
         ["Timed SQL practice"], "Begin Project 3."),
    11: ("Complete Portfolio", "Complete capstone", "Interview review",
         ["Timed SQL practice"], "Finish Project 3 and project walkthroughs."),
    12: ("Launch Job Search", "Finish certification", "PL-300 review",
         ["Interview SQL review"], "Polish portfolio and begin applications."),
}

SQL_COMPANION = [
    ("Histogram of Tweets", "Easy", "Aggregation", "COUNT, GROUP BY", 1, 20),
    ("Data Science Skills", "Easy", "Aggregation", "GROUP BY, HAVING", 1, 20),
    ("Page With No Likes", "Easy", "Joins", "LEFT JOIN, NULL", 1, 25),
    ("Laptop vs. Mobile Viewership", "Easy", "Conditional Logic", "CASE, COUNT", 1, 20),
    ("Duplicate Job Listings", "Easy", "Aggregation", "GROUP BY, HAVING", 1, 20),
    ("Teams Power Users", "Easy", "Aggregation", "COUNT, ORDER BY", 1, 20),
    ("Pharmacy Analytics Part 1", "Easy", "Arithmetic", "SUM, subtraction", 2, 25),
    ("Signup Activation Rate", "Medium", "Joins", "JOIN, ratios", 2, 30),
    ("User's Third Transaction", "Medium", "Window Functions", "ROW_NUMBER", 3, 35),
    ("Second Highest Salary", "Medium", "Ranking", "DENSE_RANK", 3, 30),
    ("Top Three Salaries", "Medium", "Ranking", "PARTITION BY", 4, 40),
    ("Tweets' Rolling Averages", "Medium", "Window Functions", "AVG OVER", 4, 40),
]
