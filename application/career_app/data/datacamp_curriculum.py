from __future__ import annotations

"""Required DataCamp chapter schedule for the 12-week Data Analytics pathway.

Every row is one planner task.  URLs are deliberately stored explicitly so the
application opens the assigned Campus chapter instead of a generic course page.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable


@dataclass(frozen=True)
class DataCampChapter:
    key: str
    course_name: str
    course_slug: str
    chapter_number: int
    chapter_name: str
    chapter_slug: str
    week: int
    weekday: int  # Monday=0
    order_in_day: int = 1
    estimated_minutes: int = 45
    area: str = "Learning"

    @property
    def url(self) -> str:
        return (
            f"https://campus.datacamp.com/courses/{self.course_slug}/"
            f"{self.chapter_slug}?ex=1"
        )

    @property
    def label(self) -> str:
        return (
            f"{self.course_name} — "
            f"Chapter {self.chapter_number}: {self.chapter_name}"
        )

    def scheduled_date(self, program_start: date) -> date:
        monday = program_start - timedelta(days=program_start.weekday())
        return monday + timedelta(days=(self.week - 1) * 7 + self.weekday)


def _chapter(
    key: str,
    course: str,
    course_slug: str,
    number: int,
    name: str,
    chapter_slug: str,
    week: int,
    weekday: int,
    order: int = 1,
    minutes: int = 45,
    area: str = "Learning",
) -> DataCampChapter:
    return DataCampChapter(
        key=key,
        course_name=course,
        course_slug=course_slug,
        chapter_number=number,
        chapter_name=name,
        chapter_slug=chapter_slug,
        week=week,
        weekday=weekday,
        order_in_day=order,
        estimated_minutes=minutes,
        area=area,
    )


DATACAMP_CHAPTERS: tuple[DataCampChapter, ...] = (
    # Week 1 — spreadsheet foundations. Saturday remains local practice/catch-up.
    _chapter("w01_intro_sheets_01", "Introduction to Google Sheets", "introduction-to-google-sheets", 1, "Cells and Formulas", "cells-and-formulas", 1, 0, area="Spreadsheets"),
    _chapter("w01_intro_sheets_02", "Introduction to Google Sheets", "introduction-to-google-sheets", 2, "Cell References", "cell-references", 1, 1, area="Spreadsheets"),
    _chapter("w01_analysis_sheets_01", "Data Analysis in Google Sheets", "data-analysis-in-google-sheets", 1, "Exploring Data", "exploring-data-1", 1, 2, area="Spreadsheets"),
    _chapter("w01_analysis_sheets_02", "Data Analysis in Google Sheets", "data-analysis-in-google-sheets", 2, "Cleaning and Preparing Data", "cleaning-and-preparing-data", 1, 3, area="Spreadsheets"),
    _chapter("w01_analysis_sheets_03", "Data Analysis in Google Sheets", "data-analysis-in-google-sheets", 3, "Analyzing Data", "analyzing-data-3", 1, 4, area="Spreadsheets"),
    _chapter("w01_intermediate_sheets_01", "Intermediate Google Sheets", "intermediate-google-sheets", 1, "What's in a Cell?", "whats-in-a-cell", 1, 6, area="Spreadsheets"),

    # Week 2 — intermediate spreadsheets and pivot tables.
    _chapter("w02_intermediate_sheets_02", "Intermediate Google Sheets", "intermediate-google-sheets", 2, "Working with Numbers", "working-with-numbers", 2, 0, area="Spreadsheets"),
    _chapter("w02_intermediate_sheets_03", "Intermediate Google Sheets", "intermediate-google-sheets", 3, "Logic & Errors", "logic-errors", 2, 1, area="Spreadsheets"),
    _chapter("w02_intermediate_sheets_04", "Intermediate Google Sheets", "intermediate-google-sheets", 4, "Positional Matching", "positional-matching", 2, 2, area="Spreadsheets"),
    _chapter("w02_pivot_sheets_01", "Pivot Tables in Google Sheets", "pivot-tables-in-google-sheets", 1, "Introduction to Pivot Tables for Google Sheets", "introduction-to-pivot-tables-for-google-sheets", 2, 3, area="Spreadsheets"),
    _chapter("w02_pivot_sheets_02", "Pivot Tables in Google Sheets", "pivot-tables-in-google-sheets", 2, "Behind the Scenes of the Pivot Table", "behind-the-scenes-of-the-pivot-table", 2, 4, area="Spreadsheets"),
    _chapter("w02_pivot_sheets_03", "Pivot Tables in Google Sheets", "pivot-tables-in-google-sheets", 3, "Advanced Options", "advanced-options", 2, 5, area="Spreadsheets"),
    _chapter("w02_pivot_sheets_04", "Pivot Tables in Google Sheets", "pivot-tables-in-google-sheets", 4, "Editing Data and Troubleshooting", "editing-data-and-troubleshooting", 2, 6, area="Spreadsheets"),

    # Week 3 — SQL foundations and the first join chapter.
    _chapter("w03_intro_sql_01", "Introduction to SQL", "introduction-to-sql", 1, "Relational Databases", "relational-databases", 3, 0, area="SQL"),
    _chapter("w03_intro_sql_02", "Introduction to SQL", "introduction-to-sql", 2, "Querying", "querying", 3, 1, area="SQL"),
    _chapter("w03_intermediate_sql_01", "Intermediate SQL", "intermediate-sql", 1, "Selecting Data", "selecting-data", 3, 2, area="SQL"),
    _chapter("w03_intermediate_sql_02", "Intermediate SQL", "intermediate-sql", 2, "Filtering Records", "filtering-records-2", 3, 3, area="SQL"),
    _chapter("w03_intermediate_sql_03", "Intermediate SQL", "intermediate-sql", 3, "Aggregate Functions", "aggregate-functions-3", 3, 4, area="SQL"),
    _chapter("w03_intermediate_sql_04", "Intermediate SQL", "intermediate-sql", 4, "Sorting and Grouping", "sorting-and-grouping-4", 3, 5, area="SQL"),
    _chapter("w03_joining_sql_01", "Joining Data in SQL", "joining-data-in-sql", 1, "Introducing Inner Joins", "introducing-inner-joins", 3, 6, area="SQL"),

    # Week 4 — joins, set theory, subqueries, CASE, CTEs, windows.
    _chapter("w04_joining_sql_02", "Joining Data in SQL", "joining-data-in-sql", 2, "Outer Joins, Cross Joins and Self Joins", "outer-joins-cross-joins-and-self-joins", 4, 0, area="SQL"),
    _chapter("w04_joining_sql_03", "Joining Data in SQL", "joining-data-in-sql", 3, "Set Theory for SQL Joins", "set-theory-for-sql-joins", 4, 1, area="SQL"),
    _chapter("w04_joining_sql_04", "Joining Data in SQL", "joining-data-in-sql", 4, "Subqueries", "subqueries-4", 4, 2, area="SQL"),
    _chapter("w04_manipulation_sql_01", "Data Manipulation in SQL", "data-manipulation-in-sql", 1, "We'll Take the CASE", "well-take-the-case", 4, 3, area="SQL"),
    _chapter("w04_manipulation_sql_02", "Data Manipulation in SQL", "data-manipulation-in-sql", 2, "Short and Simple Subqueries", "short-and-simple-subqueries", 4, 4, area="SQL"),
    _chapter("w04_manipulation_sql_03", "Data Manipulation in SQL", "data-manipulation-in-sql", 3, "Correlated Queries, Nested Queries, and Common Table Expressions", "correlated-queries-nested-queries-and-common-table-expressions", 4, 5, area="SQL"),
    _chapter("w04_manipulation_sql_04", "Data Manipulation in SQL", "data-manipulation-in-sql", 4, "Window Functions", "window-functions-4", 4, 6, area="SQL"),

    # Week 5 — windows plus PostgreSQL data/date functions.
    _chapter("w05_window_sql_01", "PostgreSQL Summary Stats and Window Functions", "postgresql-summary-stats-and-window-functions", 1, "Introduction to Window Functions", "introduction-to-window-functions", 5, 0, area="SQL"),
    _chapter("w05_window_sql_02", "PostgreSQL Summary Stats and Window Functions", "postgresql-summary-stats-and-window-functions", 2, "Fetching, Ranking, and Paging", "fetching-ranking-and-paging", 5, 1, area="SQL"),
    _chapter("w05_window_sql_03", "PostgreSQL Summary Stats and Window Functions", "postgresql-summary-stats-and-window-functions", 3, "Aggregate Window Functions and Frames", "aggregate-window-functions-and-frames", 5, 2, area="SQL"),
    _chapter("w05_window_sql_04", "PostgreSQL Summary Stats and Window Functions", "postgresql-summary-stats-and-window-functions", 4, "Beyond Window Functions", "beyond-window-functions", 5, 3, area="SQL"),
    _chapter("w05_functions_sql_01", "Functions for Manipulating Data in PostgreSQL", "functions-for-manipulating-data-in-postgresql", 1, "Overview of Common Data Types", "overview-of-common-data-types", 5, 4, area="SQL"),
    _chapter("w05_functions_sql_02", "Functions for Manipulating Data in PostgreSQL", "functions-for-manipulating-data-in-postgresql", 2, "Working with DATE/TIME Functions and Operators", "working-with-datetime-functions-and-operators", 5, 5, area="SQL"),
    _chapter("w05_functions_sql_03", "Functions for Manipulating Data in PostgreSQL", "functions-for-manipulating-data-in-postgresql", 3, "Parsing and Manipulating Text", "parsing-and-manipulating-text", 5, 6, area="SQL"),

    # Week 6 — complete SQL functions and database design.
    _chapter("w06_functions_sql_04", "Functions for Manipulating Data in PostgreSQL", "functions-for-manipulating-data-in-postgresql", 4, "Full-Text Search and PostgresSQL Extensions", "full-text-search-and-postgressql-extensions", 6, 0, area="SQL"),
    _chapter("w06_database_design_01", "Database Design", "database-design", 1, "Processing, Storing, and Organizing Data", "processing-storing-and-organizing-data", 6, 1, area="SQL"),
    _chapter("w06_database_design_02", "Database Design", "database-design", 2, "Database Schemas and Normalization", "database-schemas-and-normalization", 6, 2, area="SQL"),
    _chapter("w06_database_design_03", "Database Design", "database-design", 3, "Database Views", "database-views", 6, 3, area="SQL"),
    _chapter("w06_database_design_04", "Database Design", "database-design", 4, "Database Management", "database-management", 6, 4, area="SQL"),

    # Week 7 — Power BI intensive. Every multi-chapter course spans multiple days.
    _chapter("w07_intro_powerbi_01", "Introduction to Power BI", "introduction-to-power-bi", 1, "Getting Started with Power BI", "getting-started-with-power-bi", 7, 0, 1, area="Power BI"),
    _chapter("w07_intro_powerbi_02", "Introduction to Power BI", "introduction-to-power-bi", 2, "Transforming Data", "transforming-data-2", 7, 0, 2, area="Power BI"),
    _chapter("w07_prep_powerbi_01", "Data Preparation in Power BI", "data-preparation-in-power-bi", 1, "Profiling Your Data and Introduction to Power Query", "profiling-your-data-and-introduction-to-power-query", 7, 0, 3, area="Power BI"),
    _chapter("w07_intro_powerbi_03", "Introduction to Power BI", "introduction-to-power-bi", 3, "Visualizing Data", "visualizing-data-3", 7, 1, 1, area="Power BI"),
    _chapter("w07_intro_powerbi_04", "Introduction to Power BI", "introduction-to-power-bi", 4, "Filtering", "filtering", 7, 1, 2, area="Power BI"),
    _chapter("w07_prep_powerbi_02", "Data Preparation in Power BI", "data-preparation-in-power-bi", 2, "Data Preview Features in Power Query", "data-preview-features-in-power-query", 7, 1, 3, area="Power BI"),
    _chapter("w07_prep_powerbi_03", "Data Preparation in Power BI", "data-preparation-in-power-bi", 3, "Data Manipulation", "data-manipulation-3", 7, 2, 1, area="Power BI"),
    _chapter("w07_prep_powerbi_04", "Data Preparation in Power BI", "data-preparation-in-power-bi", 4, "Numerical Transformations in Power Query", "numerical-transformations-in-power-query", 7, 2, 2, area="Power BI"),
    _chapter("w07_model_powerbi_01", "Data Modeling in Power BI", "data-modeling-in-power-bi", 1, "Defining Tables", "defining-tables", 7, 2, 3, area="Power BI"),
    _chapter("w07_model_powerbi_02", "Data Modeling in Power BI", "data-modeling-in-power-bi", 2, "Shaping Tables", "shaping-tables", 7, 3, 1, area="Power BI"),
    _chapter("w07_model_powerbi_03", "Data Modeling in Power BI", "data-modeling-in-power-bi", 3, "Dimensional Modeling", "dimensional-modeling-3", 7, 3, 2, area="Power BI"),
    _chapter("w07_dax_powerbi_01", "Introduction to DAX in Power BI", "introduction-to-dax-in-power-bi", 1, "Getting Started with DAX", "getting-started-with-dax", 7, 3, 3, area="Power BI"),
    _chapter("w07_model_powerbi_04", "Data Modeling in Power BI", "data-modeling-in-power-bi", 4, "Star and Snowflake Schemas", "star-and-snowflake-schemas", 7, 4, 1, area="Power BI"),
    _chapter("w07_dax_powerbi_02", "Introduction to DAX in Power BI", "introduction-to-dax-in-power-bi", 2, "Context in DAX Formulas", "context-in-dax-formulas", 7, 4, 2, area="Power BI"),
    _chapter("w07_visual_powerbi_01", "Data Visualization in Power BI", "data-visualization-in-power-bi", 1, "The Audience Is King", "the-audience-is-king", 7, 4, 3, area="Power BI"),
    _chapter("w07_dax_powerbi_03", "Introduction to DAX in Power BI", "introduction-to-dax-in-power-bi", 3, "Working with Dates", "working-with-dates", 7, 5, 1, area="Power BI"),
    _chapter("w07_visual_powerbi_02", "Data Visualization in Power BI", "data-visualization-in-power-bi", 2, "Getting an Emotional Response", "getting-an-emotional-response", 7, 5, 2, area="Power BI"),
    _chapter("w07_visual_powerbi_03", "Data Visualization in Power BI", "data-visualization-in-power-bi", 3, "Reducing Cognitive Load", "reducing-cognitive-load", 7, 5, 3, area="Power BI"),
    _chapter("w07_churn_powerbi_01", "Case Study: Analyzing Customer Churn in Power BI", "case-study-analyzing-customer-churn-in-power-bi", 1, "Exploratory Analysis", "exploratory-analysis-27432f69-d260-441c-9839-c15c36c1c3f1", 7, 5, 4, area="Power BI"),
    _chapter("w07_visual_powerbi_04", "Data Visualization in Power BI", "data-visualization-in-power-bi", 4, "Less Is More", "less-is-more", 7, 6, 1, area="Power BI"),
    _chapter("w07_churn_powerbi_02", "Case Study: Analyzing Customer Churn in Power BI", "case-study-analyzing-customer-churn-in-power-bi", 2, "Investigating Churn Patterns", "investigating-churn-patterns-2", 7, 6, 2, area="Power BI"),
    _chapter("w07_churn_powerbi_03", "Case Study: Analyzing Customer Churn in Power BI", "case-study-analyzing-customer-churn-in-power-bi", 3, "Visualizing Your Analysis", "visualizing-your-analysis-3", 7, 6, 3, area="Power BI"),

    # Week 8 — analyst-focused Python and pandas.
    _chapter("w08_intro_python_01", "Introduction to Python", "intro-to-python-for-data-science", 1, "Python Basics", "chapter-1-python-basics", 8, 0, 1, area="Python"),
    _chapter("w08_intro_python_02", "Introduction to Python", "intro-to-python-for-data-science", 2, "Python Lists", "chapter-2-python-lists", 8, 0, 2, area="Python"),
    _chapter("w08_intro_python_03", "Introduction to Python", "intro-to-python-for-data-science", 3, "Functions and Packages", "chapter-3-functions-and-packages", 8, 1, 1, area="Python"),
    _chapter("w08_intro_python_04", "Introduction to Python", "intro-to-python-for-data-science", 4, "NumPy", "chapter-4-numpy", 8, 1, 2, area="Python"),
    _chapter("w08_intermediate_python_01", "Intermediate Python", "intermediate-python", 1, "Matplotlib", "matplotlib", 8, 2, 1, area="Python"),
    _chapter("w08_intermediate_python_02", "Intermediate Python", "intermediate-python", 2, "Dictionaries & pandas", "dictionaries-pandas", 8, 2, 2, area="Python"),
    _chapter("w08_intermediate_python_03", "Intermediate Python", "intermediate-python", 3, "Logic, Control Flow, and Filtering", "logic-control-flow-and-filtering", 8, 3, area="Python"),
    _chapter("w08_intermediate_python_04", "Intermediate Python", "intermediate-python", 4, "Loops", "loops", 8, 4, 1, area="Python"),
    _chapter("w08_intermediate_python_05", "Intermediate Python", "intermediate-python", 5, "Case Study: Hacker Statistics", "case-study-hacker-statistics", 8, 4, 2, area="Python"),
    _chapter("w08_pandas_01", "Data Manipulation with pandas", "data-manipulation-with-pandas", 1, "Transforming DataFrames", "transforming-dataframes", 8, 5, 1, area="Python"),
    _chapter("w08_pandas_02", "Data Manipulation with pandas", "data-manipulation-with-pandas", 2, "Aggregating DataFrames", "aggregating-dataframes", 8, 5, 2, area="Python"),
    _chapter("w08_pandas_03", "Data Manipulation with pandas", "data-manipulation-with-pandas", 3, "Slicing and Indexing DataFrames", "slicing-and-indexing-dataframes", 8, 6, 1, area="Python"),
    _chapter("w08_pandas_04", "Data Manipulation with pandas", "data-manipulation-with-pandas", 4, "Creating and Visualizing DataFrames", "creating-and-visualizing-dataframes", 8, 6, 2, area="Python"),
)

CHAPTER_BY_KEY = {chapter.key: chapter for chapter in DATACAMP_CHAPTERS}


def chapters_for_week(week: int) -> tuple[DataCampChapter, ...]:
    return tuple(chapter for chapter in DATACAMP_CHAPTERS if chapter.week == int(week))


def chapter_for_key(key: str | None) -> DataCampChapter | None:
    return CHAPTER_BY_KEY.get(str(key or "").strip())


def iter_before(chapter: DataCampChapter) -> Iterable[DataCampChapter]:
    """Yield every required chapter scheduled before ``chapter``.

    ``order_in_day`` matters during intensive weeks: a second chapter assigned
    on the same date remains locked until the earlier chapter is complete.
    """
    target = (chapter.week, chapter.weekday, chapter.order_in_day)
    return (
        item
        for item in DATACAMP_CHAPTERS
        if (item.week, item.weekday, item.order_in_day) < target
    )
