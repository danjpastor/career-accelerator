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
        "Follow the next verified DataCamp chapter selected by the adaptive track.",
        ["Histogram of Tweets", "Data Science Skills"],
        "Choose a first portfolio problem and document the audience and business context.",
    ),
    2: (
        "Ask Better Questions",
        "Finish Google Course 1 and begin Course 2.",
        "Continue the next verified DataCamp SQL chapter selected by the adaptive track.",
        ["Page With No Likes", "Laptop vs. Mobile Viewership"],
        "Draft the Project 1 charter, stakeholders, objectives, and success measures.",
    ),
    3: (
        "Prepare Reliable Data",
        "Finish Google Course 2 and begin Course 3.",
        "Continue the verified DataCamp curriculum while applying the concepts in practice.",
        ["Duplicate Job Listings", "Teams Power Users"],
        "Identify or generate the Project 1 dataset and begin the data dictionary.",
    ),
    4: (
        "Process and Clean",
        "Finish Google Course 3 and begin Course 4.",
        "Continue the verified DataCamp curriculum aligned to cleaning and validation.",
        ["Pharmacy Analytics Part 1"],
        "Validate the dataset, document quality issues, and draft the analytical schema.",
    ),
    5: (
        "Analyze With Confidence",
        "Finish Google Course 4 and begin Course 5.",
        "Continue the verified DataCamp SQL curriculum aligned to analysis.",
        ["Signup Activation Rate"],
        "Create the Project 1 SQL schema and begin the core analysis.",
    ),
    6: (
        "Analytical SQL",
        "Complete Google Course 5.",
        "Continue the verified DataCamp SQL curriculum through advanced querying.",
        ["User's Third Transaction", "Second Highest Salary"],
        "Complete the main Project 1 SQL analysis and validate the findings.",
    ),
    7: (
        "Share the Story",
        "Begin and progress through Google Course 6.",
        "Continue the verified DataCamp Power BI curriculum.",
        ["Top Three Salaries", "Tweets' Rolling Averages"],
        "Build the first Project 1 dashboard prototype.",
    ),
    8: (
        "Act on Insights",
        "Finish Google Course 6 and begin Course 7.",
        "Continue the verified DataCamp Python and pandas curriculum.",
        ["Odd and Even Measurements"],
        "Refine the dashboard, recommendations, and executive narrative.",
    ),
    9: (
        "Complete the Capstone",
        "Complete Google Course 7 and begin Course 8.",
        "Continue the next verified DataCamp chapter while prioritizing project application.",
        ["User Shopping Sprees"],
        "Publish Project 1 with a polished README, screenshots, and presentation notes.",
    ),
    10: (
        "Career Positioning",
        "Complete Google Course 8 and begin Course 9.",
        "Continue the next verified DataCamp chapter and timed SQL explanation practice.",
        ["Supercloud Customer"],
        "Begin Project 2 and translate Project 1 into résumé and interview evidence.",
    ),
    11: (
        "Portfolio Depth",
        "Complete Google Course 9 and the certificate.",
        "Continue the next verified DataCamp chapter and interview SQL practice.",
        ["Second Day Confirmation"],
        "Complete Project 2 and prepare the structure or dataset for Project 3.",
    ),
    12: (
        "Launch the Search",
        "Review certificate notes and close any remaining learning gaps.",
        "Finish remaining verified DataCamp chapters and rehearse interview patterns.",
        ["Timed SQL review"],
        "Polish the portfolio, tailor application materials, and begin a consistent job-search cadence.",
    ),
}


DATACAMP_CURRICULUM_VERSION = "2026-07-14"

DATACAMP_TRACK = [
    (
        'Introduction to SQL',
        'Chapter 1: Relational Databases',
        50,
    ),
    (
        'Introduction to SQL',
        'Chapter 2: Querying',
        70,
    ),
    (
        'Intermediate SQL',
        'Chapter 1: Data Aggregation',
        50,
    ),
    (
        'Intermediate SQL',
        'Chapter 2: Data Transformation',
        50,
    ),
    (
        'Intermediate SQL',
        'Chapter 3: Data Filtering',
        50,
    ),
    (
        'Intermediate SQL',
        'Chapter 4: Conditional Operations',
        50,
    ),
    (
        'Joining Data in SQL',
        'Chapter 1: Combining Data Vertically',
        60,
    ),
    (
        'Joining Data in SQL',
        'Chapter 2: Combining Data Horizontally',
        60,
    ),
    (
        'Data Manipulation in SQL',
        "Chapter 1: We'll take the CASE",
        60,
    ),
    (
        'Data Manipulation in SQL',
        'Chapter 2: Short and Simple Subqueries',
        60,
    ),
    (
        'Data Manipulation in SQL',
        'Chapter 3: Correlated Queries, Nested Queries, and Common Table Expressions',
        70,
    ),
    (
        'Data Manipulation in SQL',
        'Chapter 4: Window Functions',
        60,
    ),
    (
        'Introduction to Power BI',
        'Chapter 1: Getting Started with Power BI',
        45,
    ),
    (
        'Introduction to Power BI',
        'Chapter 2: Transforming Data',
        45,
    ),
    (
        'Introduction to Power BI',
        'Chapter 3: Visualizing Data',
        45,
    ),
    (
        'Introduction to Power BI',
        'Chapter 4: Filtering',
        45,
    ),
    (
        'Data Modeling in Power BI',
        'Chapter 1: Defining Tables',
        45,
    ),
    (
        'Data Modeling in Power BI',
        'Chapter 2: Shaping Tables',
        45,
    ),
    (
        'Data Modeling in Power BI',
        'Chapter 3: Dimensional Modeling',
        45,
    ),
    (
        'Data Modeling in Power BI',
        'Chapter 4: Star and Snowflake schemas',
        45,
    ),
    (
        'Introduction to Python',
        'Chapter 1: Python Basics',
        50,
    ),
    (
        'Introduction to Python',
        'Chapter 2: Python Lists',
        50,
    ),
    (
        'Introduction to Python',
        'Chapter 3: Functions and Packages',
        50,
    ),
    (
        'Introduction to Python',
        'Chapter 4: NumPy',
        60,
    ),
    (
        'Data Manipulation with pandas',
        'Chapter 1: Transforming DataFrames',
        60,
    ),
    (
        'Data Manipulation with pandas',
        'Chapter 2: Aggregating DataFrames',
        60,
    ),
    (
        'Data Manipulation with pandas',
        'Chapter 3: Slicing and Indexing DataFrames',
        60,
    ),
    (
        'Data Manipulation with pandas',
        'Chapter 4: Creating and Visualizing DataFrames',
        70,
    ),
]

SQL_COMPANION = [
    ("Histogram of Tweets", "Easy", "Multi-step Aggregation", "COUNT, GROUP BY, subquery or CTE", 6, 30),
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
