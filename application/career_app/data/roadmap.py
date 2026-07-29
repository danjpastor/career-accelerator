from career_app.data import google_certificate_curriculum as google_curriculum
from career_app.onboarding.portfolio_catalog import (
    load_project_catalog as _load_project_catalog,
)

_DEFAULT_PROJECT_NAMES = {
    1: "VFX Production Intelligence Dashboard",
    2: "Retail Operations Performance Dashboard",
    3: "Movie Industry Financial Analytics",
}

_DEFAULT_PROJECT_DIRS = {
    1: "project-01-vfx-production-intelligence",
    2: "project-02-retail-operations",
    3: "project-03-movie-industry-financial-analytics",
}

_project_catalog = _load_project_catalog()
PROJECT_NAMES = (
    dict(_project_catalog.names)
    if _project_catalog.explicit
    else dict(_DEFAULT_PROJECT_NAMES)
)
PROJECT_DIRS = (
    dict(_project_catalog.directories)
    if _project_catalog.explicit
    else dict(_DEFAULT_PROJECT_DIRS)
)

PROJECT_STAGES = [
    "Overview", "Tasks", "Dataset", "SQL", "Python", "Power BI",
    "GitHub", "README", "Resume Bullet", "Presentation", "Reflection",
]

WEEKLY_GUIDANCE = {
    1: (
        "Spreadsheet Foundations",
        f"Google priority: {google_curriculum.roadmap_summary(1)}",
        "Complete the assigned DataCamp spreadsheet chapters and local workbook practice.",
        [],
        "Portfolio preparation only: review the project brief, confirm the business problem, and preserve untouched raw data.",
    ),
    2: (
        "Spreadsheet Analysis & Mastery",
        f"Google priority: {google_curriculum.roadmap_summary(2)}",
        "Complete spreadsheet cleaning, validation, lookups, pivots, KPI analysis, and the Week 2 Knowledge Check.",
        [],
        "Portfolio preparation only: finish source documentation, the data dictionary, and preliminary relationship mapping. Do not clean or analyze portfolio data yet.",
    ),
    3: (
        "SQL Foundations & Aggregation",
        f"Google priority: {google_curriculum.roadmap_summary(3)}",
        "Complete SQL selection, filtering, sorting, aggregation, grouping, HAVING, arithmetic, and introductory CASE lessons.",
        ["Data Science Skills", "Pharmacy Analytics Part 1", "Histogram of Tweets", "Duplicate Job Listings"],
        "Portfolio preparation only: refine business questions, KPI definitions, and the analysis plan.",
    ),
    4: (
        "Relationships & Joins",
        f"Google priority: {google_curriculum.roadmap_summary(4)}",
        "Complete table grain, keys, joins, set operations, relationship validation, and the Week 4 cumulative check.",
        ["Laptop vs. Mobile Viewership", "Page With No Likes", "Signup Activation Rate", "Second Day Confirmation", "Supercloud Customer"],
        "Portfolio preparation only: finalize the relationship map and planned validation checks.",
    ),
    5: (
        "Cleaning, Subqueries & CTEs",
        f"Google priority: {google_curriculum.roadmap_summary(5)}",
        "Complete SQL cleaning functions, type conversion, CASE, subqueries, CTEs, and reproducible query workflows.",
        ["Teams Power Users", "Second Highest Salary", "User's Third Transaction", "Top Three Salaries", "Odd and Even Measurements", "Tweets' Rolling Averages", "User Shopping Sprees"],
        "Portfolio preparation only: finish the cleaning plan, validation plan, and decision log templates.",
    ),
    6: (
        "Advanced SQL Mastery",
        f"Google priority: {google_curriculum.roadmap_summary(6)}",
        "Complete window functions, date analysis, advanced SQL workflows, and the Week 6 Knowledge Check.",
        [],
        "Portfolio execution remains locked until the learning-phase mastery gates are passed.",
    ),
    7: (
        "Power BI & Power Query",
        f"Google priority: {google_curriculum.roadmap_summary(7)}",
        "Complete Power Query, data modeling, DAX foundations, report design, and the Week 7 Knowledge Check.",
        [],
        "Portfolio preparation may continue, but dashboard construction waits for Power BI mastery and final portfolio readiness.",
    ),
    8: (
        "Python, pandas & Portfolio Readiness",
        f"Google priority: {google_curriculum.roadmap_summary(8)}",
        "Complete Python and pandas foundations, cleaning, grouping, merging, notebooks, and the Week 8 Knowledge Check.",
        ["Mixed SQL retention review"],
        "Pass the Week 8 Knowledge Check to unlock cleaning, analysis, modeling, and dashboard execution.",
    ),
    9: (
        "Flagship Project — Clean & Analyze",
        f"Google priority: {google_curriculum.roadmap_summary(9)}",
        "Apply spreadsheet, SQL, Power BI, and Python skills to the flagship project with validation at every stage.",
        ["Targeted SQL retention"],
        "Clean and validate Project 1, build the analytical database, complete SQL and exploratory analysis, and reconcile findings.",
    ),
    10: (
        "Flagship Project — Model, Report & Publish",
        f"Google priority: {google_curriculum.roadmap_summary(10)}",
        "Apply Power Query, modeling, DAX, report design, and communication skills to Project 1.",
        ["Targeted interview review"],
        "Complete the Power BI model and report, executive summary, recommendations, README, and reproducible publication for Project 1.",
    ),
    11: (
        "Portfolio Projects 2 & 3",
        f"Google priority: {google_curriculum.roadmap_summary(11)}",
        "Use targeted practice to support the specific skills required by Projects 2 and 3.",
        ["Mixed interview practice"],
        "Complete a focused Project 2 and begin or substantially complete Project 3 with distinct business capabilities.",
    ),
    12: (
        "Portfolio QA & Career Launch",
        f"Google priority: {google_curriculum.roadmap_summary(12)}",
        "Complete final mastery remediation, SQL review, and project walkthrough practice.",
        ["Timed SQL review"],
        "Finish Project 3, audit all projects, publish final versions, update résumé and LinkedIn, rehearse interviews, and begin targeted applications.",
    ),
}


APPLIED_LAB_SUMMARY = {3: ['Google Sheets analyst spreadsheet'],
 4: ['Descriptive statistics and distributions',
     'SQL validation checklist',
     'Broken join diagnosis'],
 5: ['Sampling and bias', 'Conversion funnel', 'Executive summary and memo', 'KPI repair'],
 6: ['Confidence intervals', 'Misleading story repair', 'Timed missed-deadlines request'],
 7: ['Hypothesis testing',
     'Cohort retention',
     'Power BI import/profile',
     'Power Query transformations'],
 8: ['A/B-test analysis',
     'Churn analysis',
     'Power BI model and DAX',
     'pandas loading and cleaning'],
 9: ['Correlation versus causation',
     'Forecast-versus-actual variance',
     'API and JSON ingestion',
     'Power BI report and deployment',
     'Dashboard walkthrough'],
 10: ['Linear regression interpretation',
      'Raw-to-analytics pipeline',
      'pandas outputs and SQL parity',
      'Finance reconciliation'],
 11: ['Responsible AI audit', 'Decision log', 'Responsible metric response'],
 12: ['Optional Power BI performance optimization']}

DATALEMUR_PROBLEM_URLS = {
    "Histogram of Tweets": "https://datalemur.com/questions/sql-histogram-tweets",
    "Data Science Skills": "https://datalemur.com/questions/matching-skills",
    "Page With No Likes": "https://datalemur.com/questions/sql-page-with-no-likes",
    "Laptop vs. Mobile Viewership": "https://datalemur.com/questions/laptop-mobile-viewership",
    "Duplicate Job Listings": "https://datalemur.com/questions/duplicate-job-listings",
    "Teams Power Users": "https://datalemur.com/questions/teams-power-users",
    "Pharmacy Analytics Part 1": "https://datalemur.com/questions/top-profitable-drugs",
    "Signup Activation Rate": "https://datalemur.com/questions/signup-confirmation-rate",
    "User's Third Transaction": "https://datalemur.com/questions/sql-third-transaction",
    "Second Highest Salary": "https://datalemur.com/questions/sql-second-highest-salary",
    "Top Three Salaries": "https://datalemur.com/questions/sql-top-three-salaries",
    "Tweets' Rolling Averages": "https://datalemur.com/questions/rolling-average-tweets",
    "Odd and Even Measurements": "https://datalemur.com/questions/odd-even-measurements",
    "User Shopping Sprees": "https://datalemur.com/questions/amazon-shopping-spree",
    "Supercloud Customer": "https://datalemur.com/questions/supercloud-customer",
    "Second Day Confirmation": "https://datalemur.com/questions/second-day-confirmation",
}


SQL_COMPANION = [
    ("Histogram of Tweets", "Easy", "Multi-step Aggregation", "COUNT, GROUP BY, subquery or CTE", 3, 30),
    ("Data Science Skills", "Easy", "Aggregation", "GROUP BY, HAVING", 3, 20),
    ("Page With No Likes", "Easy", "Joins", "LEFT JOIN, NULL", 4, 25),
    ("Laptop vs. Mobile Viewership", "Easy", "Conditional Logic", "CASE, COUNT", 4, 20),
    ("Duplicate Job Listings", "Easy", "Aggregation", "GROUP BY, HAVING", 3, 20),
    ("Teams Power Users", "Easy", "Aggregation", "COUNT, ORDER BY", 5, 20),
    ("Pharmacy Analytics Part 1", "Easy", "Arithmetic", "SUM, subtraction", 3, 25),
    ("Signup Activation Rate", "Medium", "Joins", "JOIN, ratios", 4, 30),
    ("User's Third Transaction", "Medium", "Window Functions", "ROW_NUMBER", 5, 35),
    ("Second Highest Salary", "Medium", "Ranking", "DENSE_RANK", 5, 30),
    ("Top Three Salaries", "Medium", "Ranking", "PARTITION BY", 5, 40),
    ("Tweets' Rolling Averages", "Medium", "Window Functions", "AVG OVER", 5, 40),
    ("Odd and Even Measurements", "Medium", "Window Functions", "ROW_NUMBER, SUM", 5, 40),
    ("User Shopping Sprees", "Medium", "Date Logic", "GROUP BY, dates", 5, 35),
    ("Supercloud Customer", "Medium", "Relational Division", "COUNT DISTINCT", 4, 40),
    ("Second Day Confirmation", "Medium", "Joins", "dates, filtering", 4, 35),
]
