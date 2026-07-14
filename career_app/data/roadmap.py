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
    1: (
        "Analytics Foundations",
        "Start Google Course 1 and establish a consistent study system.",
        "DataCamp Introduction to SQL: SELECT, FROM, WHERE, ORDER BY, LIMIT.",
        ["Histogram of Tweets", "Data Science Skills"],
        "Choose a first portfolio problem and document the audience and business context.",
    ),
    2: (
        "Ask Better Questions",
        "Finish Google Course 1 and begin Course 2.",
        "Continue SQL fundamentals: filtering, aggregation, GROUP BY, and HAVING.",
        ["Page With No Likes", "Laptop vs. Mobile Viewership"],
        "Draft the Project 1 charter, stakeholders, objectives, and success measures.",
    ),
    3: (
        "Prepare Reliable Data",
        "Finish Google Course 2 and begin Course 3.",
        "Practice spreadsheet analysis and SQL data exploration.",
        ["Duplicate Job Listings", "Teams Power Users"],
        "Identify or generate the Project 1 dataset and begin the data dictionary.",
    ),
    4: (
        "Process and Clean",
        "Finish Google Course 3 and begin Course 4.",
        "Practice SQL cleaning logic, NULL handling, and quality checks.",
        ["Pharmacy Analytics Part 1"],
        "Validate the dataset, document quality issues, and draft the analytical schema.",
    ),
    5: (
        "Analyze With Confidence",
        "Finish Google Course 4 and begin Course 5.",
        "Strengthen aggregations, CASE expressions, and business-metric calculations.",
        ["Signup Activation Rate"],
        "Create the Project 1 SQL schema and begin the core analysis.",
    ),
    6: (
        "Analytical SQL",
        "Complete Google Course 5.",
        "Practice joins, CTEs, subqueries, and window-function foundations.",
        ["User's Third Transaction", "Second Highest Salary"],
        "Complete the main Project 1 SQL analysis and validate the findings.",
    ),
    7: (
        "Share the Story",
        "Begin and progress through Google Course 6.",
        "Learn Power BI foundations and translate SQL outputs into measures.",
        ["Top Three Salaries", "Tweets' Rolling Averages"],
        "Build the first Project 1 dashboard prototype.",
    ),
    8: (
        "Act on Insights",
        "Finish Google Course 6 and begin Course 7.",
        "Learn analytics-focused Python and pandas fundamentals.",
        ["Odd and Even Measurements"],
        "Refine the dashboard, recommendations, and executive narrative.",
    ),
    9: (
        "Complete the Capstone",
        "Complete Google Course 7 and begin Course 8.",
        "Review SQL, Power BI, and Python through integrated project work.",
        ["User Shopping Sprees"],
        "Publish Project 1 with a polished README, screenshots, and presentation notes.",
    ),
    10: (
        "Career Positioning",
        "Complete Google Course 8 and begin Course 9.",
        "Practice medium SQL and timed explanation of completed solutions.",
        ["Supercloud Customer"],
        "Begin Project 2 and translate Project 1 into résumé and interview evidence.",
    ),
    11: (
        "Portfolio Depth",
        "Complete Google Course 9 and the certificate.",
        "Practice interview SQL, query review, and explanation under time limits.",
        ["Second Day Confirmation"],
        "Complete Project 2 and prepare the structure or dataset for Project 3.",
    ),
    12: (
        "Launch the Search",
        "Review certificate notes and close any remaining learning gaps.",
        "Complete a mixed SQL review and rehearse common interview patterns.",
        ["Timed SQL review"],
        "Polish the portfolio, tailor application materials, and begin a consistent job-search cadence.",
    ),
}


DATACAMP_TRACK = [
    (
        "Introduction to SQL",
        "Selecting columns and inspecting tables",
        30,
    ),
    (
        "Introduction to SQL",
        "Filtering rows with WHERE",
        30,
    ),
    (
        "Introduction to SQL",
        "Aggregate functions and grouped summaries",
        35,
    ),
    (
        "Intermediate SQL",
        "Sorting, grouping, and HAVING",
        35,
    ),
    (
        "Intermediate SQL",
        "CASE expressions and data types",
        40,
    ),
    (
        "Joining Data in SQL",
        "INNER and LEFT joins",
        40,
    ),
    (
        "Joining Data in SQL",
        "Outer joins and set operations",
        40,
    ),
    (
        "Data Manipulation in SQL",
        "Subqueries and common table expressions",
        45,
    ),
    (
        "Data Manipulation in SQL",
        "Window functions and ranking",
        45,
    ),
    (
        "Introduction to Power BI",
        "Loading data and building first visuals",
        45,
    ),
    (
        "Data Modeling in Power BI",
        "Relationships, measures, and DAX",
        50,
    ),
    (
        "Introduction to Python",
        "pandas DataFrames and analytical workflows",
        45,
    ),
]

SQL_COMPANION = [
    ("Histogram of Tweets", "Easy", "Aggregation", "COUNT, GROUP BY", 1, 20),
    ("Data Science Skills", "Easy", "Aggregation", "GROUP BY, HAVING", 1, 20),
    ("Page With No Likes", "Easy", "Joins", "LEFT JOIN, NULL", 2, 25),
    ("Laptop vs. Mobile Viewership", "Easy", "Conditional Logic", "CASE, COUNT", 2, 20),
    ("Duplicate Job Listings", "Easy", "Aggregation", "GROUP BY, HAVING", 3, 20),
    ("Teams Power Users", "Easy", "Aggregation", "COUNT, ORDER BY", 3, 20),
    ("Pharmacy Analytics Part 1", "Easy", "Arithmetic", "SUM, subtraction", 4, 25),
    ("Signup Activation Rate", "Medium", "Joins", "JOIN, ratios", 5, 30),
    ("User's Third Transaction", "Medium", "Window Functions", "ROW_NUMBER", 6, 35),
    ("Second Highest Salary", "Medium", "Ranking", "DENSE_RANK", 6, 30),
    ("Top Three Salaries", "Medium", "Ranking", "PARTITION BY", 7, 40),
    ("Tweets' Rolling Averages", "Medium", "Window Functions", "AVG OVER", 7, 40),
    ("Odd and Even Measurements", "Medium", "Window Functions", "ROW_NUMBER, SUM", 8, 40),
    ("User Shopping Sprees", "Medium", "Date Logic", "GROUP BY, dates", 9, 35),
    ("Supercloud Customer", "Medium", "Relational Division", "COUNT DISTINCT", 10, 40),
    ("Second Day Confirmation", "Medium", "Joins", "dates, filtering", 11, 35),
]
