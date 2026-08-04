from __future__ import annotations

"""Task-title normalization shared by planners, migrations, and workspaces.

Human-readable task labels use Title Case while preserving technical products,
acronyms, SQL clauses, and spreadsheet/Python function names that have canonical
capitalization.
"""

import re

_MINOR_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into",
    "nor", "of", "on", "or", "over", "per", "the", "to", "up", "via", "with",
}

_CANONICAL_TOKENS = {
    "sql": "SQL",
    "dax": "DAX",
    "cte": "CTE",
    "ctes": "CTEs",
    "api": "API",
    "apis": "APIs",
    "json": "JSON",
    "csv": "CSV",
    "csvs": "CSVs",
    "kpi": "KPI",
    "kpis": "KPIs",
    "id": "ID",
    "ids": "IDs",
    "url": "URL",
    "urls": "URLs",
    "ui": "UI",
    "ux": "UX",
    "qa": "QA",
    "etl": "ETL",
    "elt": "ELT",
    "excel": "Excel",
    "python": "Python",
    "pandas": "pandas",
    "numpy": "NumPy",
    "duckdb": "DuckDB",
    "github": "GitHub",
    "linkedin": "LinkedIn",
    "readme": "README",
    "powerbi": "Power BI",
    "xlookup": "XLOOKUP",
    "vlookup": "VLOOKUP",
    "sumif": "SUMIF",
    "sumifs": "SUMIFS",
    "countif": "COUNTIF",
    "countifs": "COUNTIFS",
    "averageif": "AVERAGEIF",
    "averageifs": "AVERAGEIFS",
    "iferror": "IFERROR",
    "iserror": "ISERROR",
    "select": "SELECT",
    "where": "WHERE",
    "having": "HAVING",
    "join": "JOIN",
    "union": "UNION",
    "case": "CASE",
    "null": "NULL",
    "distinct": "DISTINCT",
    "limit": "LIMIT",
    "offset": "OFFSET",
    "row_number": "ROW_NUMBER",
    "dense_rank": "DENSE_RANK",
    "rank": "RANK",
    "lag": "LAG",
    "lead": "LEAD",
    "avg": "AVG",
    "sum": "SUM",
    "count": "COUNT",
    "min": "MIN",
    "max": "MAX",
}

# Product and multi-word SQL phrases are repaired after token-level casing.
_PHRASE_REPLACEMENTS = (
    (re.compile(r"\bPower\s+Bi\b", re.I), "Power BI"),
    (re.compile(r"\bGoogle\s+Sheets\b", re.I), "Google Sheets"),
    (re.compile(r"\bGroup\s+By\b", re.I), "GROUP BY"),
    (re.compile(r"\bOrder\s+By\b", re.I), "ORDER BY"),
    (re.compile(r"\bPartition\s+By\b", re.I), "PARTITION BY"),
    (re.compile(r"\bUnion\s+All\b", re.I), "UNION ALL"),
    (re.compile(r"\bLeft\s+Join\b", re.I), "LEFT JOIN"),
    (re.compile(r"\bRight\s+Join\b", re.I), "RIGHT JOIN"),
    (re.compile(r"\bInner\s+Join\b", re.I), "INNER JOIN"),
    (re.compile(r"\bFull\s+(?:Outer\s+)?Join\b", re.I), "FULL OUTER JOIN"),
    (re.compile(r"\bCross\s+Join\b", re.I), "CROSS JOIN"),
    (re.compile(r"\bIf,?\s+And,?\s+Or\b", re.I), "IF, AND, OR"),
    (re.compile(r"\bCase\s+When\b", re.I), "CASE WHEN"),
)

_WORD_RE = re.compile(r"([^\W_][\w]*(?:['’][^\W_]+)?)", re.UNICODE)


def title_case_task(value: object) -> str:
    """Return a readable Title Case task label with technical casing preserved."""

    text = re.sub(r"\s+", " ", str(value or "").strip())
    if not text:
        return ""
    # SQL challenge titles are authored and audited in the curriculum catalog.
    # Preserve their exact human-readable capitalization instead of converting
    # ordinary words such as "Count" into SQL keyword casing.
    if text.startswith("Complete SQL Challenge "):
        return text

    words = list(_WORD_RE.finditer(text))
    if not words:
        return text
    first_start = words[0].start()
    last_start = words[-1].start()

    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        lower = token.casefold()
        canonical = _CANONICAL_TOKENS.get(lower)
        if canonical is not None:
            return canonical
        # Preserve intentionally mixed-case identifiers such as iPython only
        # when they already contain both upper- and lower-case letters.
        if token.isascii() and any(ch.isupper() for ch in token[1:]) and any(ch.islower() for ch in token):
            return token
        if match.start() not in {first_start, last_start} and lower in _MINOR_WORDS:
            return lower
        return token[:1].upper() + token[1:].lower()

    result = _WORD_RE.sub(replace, text)
    for pattern, replacement in _PHRASE_REPLACEMENTS:
        result = pattern.sub(replacement, result)
    return result


def normalize_database_task_titles(conn) -> int:
    """Normalize durable user-facing task records without changing task identity."""

    changed = 0
    for table in ("sprint_tasks", "project_tasks"):
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if not exists:
            continue
        rows = conn.execute(f"SELECT id,label FROM {table}").fetchall()
        for row in rows:
            task_id = int(row["id"] if hasattr(row, "keys") else row[0])
            label = str(row["label"] if hasattr(row, "keys") else row[1])
            normalized = title_case_task(label)
            if normalized and normalized != label:
                conn.execute(f"UPDATE {table} SET label=? WHERE id=?", (normalized, task_id))
                changed += 1
    return changed
