from datetime import date, timedelta

ENERGY_RANK = {"Low": 1, "Normal": 2, "High": 3}

DEFAULTS = {
    "Learning": (40, "Normal", 1, 2),
    "SQL": (25, "Normal", 1, 4),
    "Portfolio": (45, "High", 2, 3),
    "Review": (20, "Low", 3, 8),
    "General": (25, "Low", 3, 1),
}

def infer(label):
    lower = label.lower()
    if any(x in lower for x in ("google", "course", "module", "datacamp", "lesson", "quiz")):
        category = "Learning"
    elif any(x in lower for x in ("sql", "datalemur", "tweets", "skills", "likes", "listings")):
        category = "SQL"
    elif any(x in lower for x in ("project", "portfolio", "schema", "dataset", "charter", "kpi", "readme")):
        category = "Portfolio"
    elif any(x in lower for x in ("review", "retrospective", "summary")):
        category = "Review"
    else:
        category = "General"
    minutes, energy, priority, destination = DEFAULTS[category]
    return {
        "category": category,
        "minutes": minutes,
        "energy": energy,
        "priority": priority,
        "destination": destination,
    }

def seed(conn):
    rows = conn.execute("SELECT id,label,completed FROM sprint_tasks").fetchall()
    for row in rows:
        meta = infer(row["label"])
        existing = conn.execute(
            "SELECT task_id FROM task_metadata WHERE task_id=?", (row["id"],)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE task_metadata SET category=COALESCE(NULLIF(category,''),?) WHERE task_id=?",
                (meta["category"], row["id"]),
            )
            continue
        conn.execute(
            """INSERT INTO task_metadata
               (task_id,status,priority,estimated_minutes,energy,destination,category)
               VALUES(?,?,?,?,?,?,?)""",
            (
                row["id"],
                "Completed" if row["completed"] else "Not Started",
                meta["priority"],
                meta["minutes"],
                meta["energy"],
                meta["destination"],
                meta["category"],
            ),
        )
    conn.commit()

def available(conn, week):
    today = date.today().isoformat()
    return conn.execute(
        """SELECT s.id,s.label,s.completed,m.status,m.priority,m.estimated_minutes,
                  m.energy,m.deferred_until,m.destination,m.category
           FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE s.week=? AND m.status NOT IN ('Completed','Blocked')
             AND (m.deferred_until IS NULL OR m.deferred_until<=?)
           ORDER BY m.priority,
                    CASE m.status WHEN 'In Progress' THEN 0 ELSE 1 END,
                    s.sort_order""",
        (week, today),
    ).fetchall()

def make_plan(conn, week, minutes, energy):
    capacity = ENERGY_RANK.get(energy, 2)
    eligible = [
        row for row in available(conn, week)
        if ENERGY_RANK.get(row["energy"], 2) <= capacity
    ]
    selected = []
    remaining = max(0, minutes)
    for row in eligible:
        estimate = int(row["estimated_minutes"])
        if estimate <= remaining or not selected:
            selected.append(row)
            remaining -= estimate
        if remaining <= 5:
            break
    return selected, max(0, remaining)

def defer(conn, task_id, days=1):
    target = (date.today() + timedelta(days=days)).isoformat()
    conn.execute(
        "UPDATE task_metadata SET status='Deferred',deferred_until=? WHERE task_id=?",
        (target, task_id),
    )
    conn.commit()
