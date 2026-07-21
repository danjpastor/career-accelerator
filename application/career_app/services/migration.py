from __future__ import annotations
import json
import re
from pathlib import Path

from career_app.data.applied_exercises import APPLIED_EXERCISES
from career_app.data.duckdb_exercises import DUCKDB_EXERCISES
from career_app.data.roadmap_tasks import task_key, task_spec
from career_app.data.portfolio_tasks import task_spec as portfolio_task_spec

CHECKBOX = re.compile(r"^\s*-\s+\[([ xX])\]\s+(.+?)\s*$")

PROJECT_DIRS = {
    1: "project-01-vfx-production-intelligence",
    2: "project-02-retail-operations",
    3: "project-03-movie-industry-financial-analytics",
}

STAGE_KEYWORDS = [
    ("Discovery", ("business problem", "stakeholder", "kpi", "business question", "charter")),
    ("Dataset", ("dataset", "data dictionary", "validate", "clean")),
    ("SQL", ("schema", "sql", "query")),
    ("Python", ("python", "pandas", "eda", "anomaly")),
    ("Power BI", ("power bi", "dax", "dashboard", "measure")),
    ("GitHub", ("github", "release", "publish")),
    ("README", ("readme", "documentation", "screenshot")),
    ("Resume Bullet", ("resume", "bullet")),
    ("Presentation", ("presentation", "walkthrough")),
    ("Reflection", ("reflection", "lessons learned")),
]

def checkboxes(path: Path):
    if not path.exists():
        return []
    seen = set()
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CHECKBOX.match(line)
        if not match:
            continue
        label = match.group(2).strip()
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        rows.append((label, 1 if match.group(1).lower() == "x" else 0))
    return rows

def stage_for(label):
    lower = label.lower()
    for stage, words in STAGE_KEYWORDS:
        if any(word in lower for word in words):
            return stage
    return "Overview"




ACTIVE_DYNAMIC_TRACKS = {"google", "academy", "sql", "portfolio", "applied"}
ACADEMY_EVIDENCE_TYPES = {"Skills Lab", "Academy Project", "Academy Capstone"}


def _archive_roadmap_task(conn, row, reason: str) -> None:
    metadata = {
        "priority": row["priority"],
        "estimated_minutes": row["estimated_minutes"],
        "energy": row["energy"],
        "destination": row["destination"],
        "prerequisite_state": row["prerequisite_state"],
        "prerequisite_reason": row["prerequisite_reason"],
        "target_key": row["target_key"],
        "source_label": row["source_label"],
        "linked_entity_id": row["linked_entity_id"],
    }
    conn.execute(
        """INSERT INTO roadmap_task_archive
           (original_task_id,week,sort_order,label,completed,status,category,track_key,reason,metadata)
           VALUES(?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(original_task_id) DO UPDATE SET
               reason=excluded.reason,
               metadata=excluded.metadata""",
        (
            int(row["id"]),
            int(row["week"]),
            int(row["sort_order"]),
            str(row["label"]),
            int(row["completed"] or 0),
            row["status"],
            row["category"],
            row["track_key"],
            reason,
            json.dumps(metadata, sort_keys=True, default=str),
        ),
    )
    # Preserve any user-authored document as a historical workspace while
    # disconnecting it from the active roadmap assignment.
    conn.execute(
        "UPDATE task_workspaces SET task_id=NULL WHERE task_id=?",
        (int(row["id"]),),
    )
    # Incomplete frozen focus rows should be rebuilt from the cleaned roadmap.
    conn.execute(
        "DELETE FROM daily_focus WHERE task_id=? AND completed_at IS NULL",
        (int(row["id"]),),
    )
    conn.execute("DELETE FROM sprint_tasks WHERE id=?", (int(row["id"]),))


def _clean_legacy_roadmap_tasks(conn) -> dict:
    rows = conn.execute(
        """SELECT s.id,s.week,s.sort_order,s.label,s.completed,
                  m.status,m.priority,m.estimated_minutes,m.energy,m.destination,
                  m.category,m.prerequisite_state,m.prerequisite_reason,
                  tt.track_key,tt.target_key,tt.source_label,tt.linked_entity_id
           FROM sprint_tasks s
           LEFT JOIN task_metadata m ON m.task_id=s.id
           LEFT JOIN track_tasks tt ON tt.task_id=s.id
           ORDER BY s.week,s.sort_order,s.id"""
    ).fetchall()
    archived = 0
    retained = 0
    updated = 0
    for row in rows:
        track_key = str(row["track_key"] or "").strip().lower()
        if track_key in ACTIVE_DYNAMIC_TRACKS:
            if track_key == "academy":
                cleaned = re.sub(
                    r"^\s*\[Accelerator Academy\]\s*",
                    "",
                    str(row["label"] or ""),
                    flags=re.IGNORECASE,
                )
                cleaned = re.sub(r"^Learn:\s*", "", cleaned, flags=re.IGNORECASE)
                if cleaned and cleaned != row["label"]:
                    conn.execute(
                        "UPDATE sprint_tasks SET label=? WHERE id=?",
                        (cleaned, int(row["id"])),
                    )
            retained += 1
            continue
        if track_key == "datacamp" or "datacamp" in str(row["label"] or "").casefold():
            _archive_roadmap_task(conn, row, "Replaced by Accelerator Academy")
            archived += 1
            continue

        spec = task_spec(str(row["label"] or ""))
        if spec is None:
            _archive_roadmap_task(
                conn,
                row,
                "Historical static task replaced by a dedicated adaptive track or project milestone",
            )
            archived += 1
            continue

        conn.execute(
            """UPDATE task_metadata
               SET status=CASE WHEN ? THEN 'Completed' ELSE COALESCE(status,'Not Started') END,
                   priority=?,estimated_minutes=?,energy=?,destination=?,category=?,
                   prerequisite_state='Ready',prerequisite_reason=NULL,
                   description=?,definition_of_done=?,starter_path=?,managed_key=?
               WHERE task_id=?""",
            (
                int(row["completed"] or 0),
                spec.priority,
                spec.estimated_minutes,
                spec.energy,
                spec.destination,
                spec.category,
                spec.description,
                spec.definition_of_done,
                spec.starter_path,
                task_key(str(row["label"] or "")),
                int(row["id"]),
            ),
        )
        retained += 1
        updated += 1

    conn.execute(
        """UPDATE track_state
           SET status='Historical',weekly_target=0,
               metadata=json_set(COALESCE(metadata,'{}'),'$.replacement','Accelerator Academy'),
               updated_at=CURRENT_TIMESTAMP
           WHERE track_key='datacamp'"""
    )
    conn.execute(
        """DELETE FROM daily_focus
           WHERE completed_at IS NULL
             AND (source_key LIKE 'roadmap:%'
                  OR track_key='datacamp'
                  OR LOWER(title) LIKE '%datacamp%')"""
    )
    return {"archived": archived, "retained": retained, "updated": updated}


def _clean_academy_evidence(conn) -> dict:
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "academy_skill_evidence" not in tables:
        return {
            "academy_rows_removed": 0,
            "main_rows_removed": 0,
            "projects_consolidated": 0,
        }
    placeholders = ",".join("?" for _ in ACADEMY_EVIDENCE_TYPES)
    removed_academy = conn.execute(
        f"SELECT COUNT(*) FROM academy_skill_evidence WHERE source_type NOT IN ({placeholders})",
        tuple(sorted(ACADEMY_EVIDENCE_TYPES)),
    ).fetchone()[0]
    conn.execute(
        f"DELETE FROM academy_skill_evidence WHERE source_type NOT IN ({placeholders})",
        tuple(sorted(ACADEMY_EVIDENCE_TYPES)),
    )
    removed_main = conn.execute(
        """SELECT COUNT(*) FROM evidence
           WHERE source_type IN ('Academy Practice','Academy Mastery')"""
    ).fetchone()[0]
    conn.execute(
        """DELETE FROM evidence
           WHERE source_type IN ('Academy Practice','Academy Mastery')"""
    )
    conn.execute(
        """DELETE FROM skill_state
           WHERE source_track='academy'
             AND (evidence LIKE 'Academy Practice:%' OR evidence LIKE 'Academy Mastery:%')"""
    )

    # Keep one employer-facing evidence row per substantial Academy project,
    # even though the internal skill table records several skills per project.
    project_rows = conn.execute(
        f"""SELECT source_type,source_name,
                   GROUP_CONCAT(DISTINCT skill) AS skills,
                   MAX(description) AS description,
                   COUNT(*) AS row_count
            FROM evidence
            WHERE source_type IN ({placeholders})
            GROUP BY source_type,source_name""",
        tuple(sorted(ACADEMY_EVIDENCE_TYPES)),
    ).fetchall()
    consolidated = 0
    for row in project_rows:
        if int(row["row_count"] or 0) <= 1:
            continue
        conn.execute(
            "DELETE FROM evidence WHERE source_type=? AND source_name=?",
            (row["source_type"], row["source_name"]),
        )
        conn.execute(
            """INSERT INTO evidence(skill,source_type,source_name,description)
               VALUES(?,?,?,?)""",
            (
                row["skills"] or "Applied analysis",
                row["source_type"],
                row["source_name"],
                row["description"],
            ),
        )
        consolidated += 1
    return {
        "academy_rows_removed": int(removed_academy),
        "main_rows_removed": int(removed_main),
        "projects_consolidated": consolidated,
    }


def _update_duckdb_exercise_tasks(conn):
    updated = 0
    for exercise in DUCKDB_EXERCISES.values():
        rows = conn.execute(
            """SELECT id,label
               FROM sprint_tasks
               WHERE label IN (?,?)""",
            (
                exercise["old_label"],
                exercise["label"],
            ),
        ).fetchall()

        for row in rows:
            if row["label"] != exercise["label"]:
                conn.execute(
                    "UPDATE sprint_tasks SET label=? WHERE id=?",
                    (exercise["label"], row["id"]),
                )
                updated += 1

            conn.execute(
                """UPDATE task_metadata
                   SET category='SQL',
                       priority=?,
                       estimated_minutes=?,
                       energy='Normal',
                       destination=4
                   WHERE task_id=?""",
                (
                    exercise["priority"],
                    exercise["minutes"],
                    row["id"],
                ),
            )
    return updated



def _ensure_applied_exercise_tasks(conn):
    added = 0
    updated = 0
    for number, item in APPLIED_EXERCISES.items():
        labels = [item["label"], *item.get("aliases", [])]
        marks = ",".join("?" for _ in labels)
        rows = conn.execute(
            f"SELECT id,label,week,sort_order,completed FROM sprint_tasks WHERE label IN ({marks}) ORDER BY id",
            tuple(labels),
        ).fetchall()
        if rows:
            row = rows[0]
            task_id = int(row["id"])
            target_week = int(item["week"])
            current_week = int(row["week"])
            if current_week != target_week:
                target_sort = conn.execute(
                    "SELECT COALESCE(MAX(sort_order),0)+100 FROM sprint_tasks WHERE week=?",
                    (target_week,),
                ).fetchone()[0]
                conn.execute(
                    "UPDATE sprint_tasks SET label=?,week=?,sort_order=? WHERE id=?",
                    (item["label"], target_week, int(target_sort), task_id),
                )
                updated += 1
            elif row["label"] != item["label"]:
                conn.execute(
                    "UPDATE sprint_tasks SET label=? WHERE id=?",
                    (item["label"], task_id),
                )
                updated += 1
        else:
            sort_order = conn.execute(
                "SELECT COALESCE(MAX(sort_order),0)+100 FROM sprint_tasks WHERE week=?",
                (int(item["week"]),),
            ).fetchone()[0]
            cursor = conn.execute(
                "INSERT INTO sprint_tasks(week,sort_order,label,completed) VALUES(?,?,?,0)",
                (int(item["week"]), int(sort_order), item["label"]),
            )
            task_id = int(cursor.lastrowid)
            added += 1
        meta = conn.execute("SELECT task_id FROM task_metadata WHERE task_id=?",(task_id,)).fetchone()
        if meta is None:
            completed = conn.execute("SELECT completed FROM sprint_tasks WHERE id=?",(task_id,)).fetchone()["completed"]
            conn.execute(
                """INSERT INTO task_metadata(task_id,status,priority,estimated_minutes,energy,destination,category,prerequisite_state)
                   VALUES(?,?,?,?,?,?,?,'Ready')""",
                (task_id,'Completed' if completed else 'Not Started',int(item['priority']),int(item['minutes']),item['energy'],int(item['destination']),item['task_category']),
            )
        else:
            conn.execute(
                """UPDATE task_metadata SET priority=?,estimated_minutes=?,energy=?,destination=?,category=? WHERE task_id=?""",
                (int(item['priority']),int(item['minutes']),item['energy'],int(item['destination']),item['task_category'],task_id),
            )
    return {'added':added,'updated':updated}

def _sync_portfolio_task_guidance(conn) -> dict:
    """Attach durable guidance metadata to every portfolio milestone."""
    rows = conn.execute(
        """SELECT id,project_id,label,description,definition_of_done,
                  starter_path,estimated_minutes,managed_key
           FROM project_tasks
           ORDER BY project_id,sort_order"""
    ).fetchall()
    updated = 0
    missing = []
    for row in rows:
        spec = portfolio_task_spec(row["label"], int(row["project_id"]))
        if spec is None:
            missing.append(str(row["label"]))
            continue
        values = (
            spec.description,
            spec.definition_of_done,
            spec.starter_path,
            int(spec.estimated_minutes),
            spec.key,
            int(row["id"]),
        )
        current = (
            str(row["description"] or ""),
            str(row["definition_of_done"] or ""),
            str(row["starter_path"] or ""),
            int(row["estimated_minutes"] or 45),
            str(row["managed_key"] or ""),
        )
        desired = values[:-1]
        if current != desired:
            conn.execute(
                """UPDATE project_tasks
                   SET description=?,definition_of_done=?,starter_path=?,
                       estimated_minutes=?,managed_key=?
                   WHERE id=?""",
                values,
            )
            updated += 1

        linked = conn.execute(
            """SELECT tt.task_id,m.estimated_minutes
               FROM track_tasks tt
               JOIN task_metadata m ON m.task_id=tt.task_id
               WHERE tt.track_key='portfolio'
                 AND tt.linked_entity_id=?""",
            (int(row["id"]),),
        ).fetchone()
        if linked is not None:
            conn.execute(
                """UPDATE task_metadata
                   SET description=?,definition_of_done=?,starter_path=?,managed_key=?,
                       estimated_minutes=CASE
                           WHEN estimated_minutes=45 THEN ?
                           ELSE estimated_minutes
                       END
                   WHERE task_id=?""",
                (
                    spec.description,
                    spec.definition_of_done,
                    spec.starter_path,
                    f"portfolio:{int(row['project_id'])}:{int(row['id'])}",
                    int(spec.estimated_minutes),
                    int(linked["task_id"]),
                ),
            )
    return {
        "updated": updated,
        "missing": sorted(set(missing)),
        "total": len(rows),
    }


def migrate(conn, root: Path):
    sprint_count = 0
    project_count = 0

    for week in range(1, 13):
        existing = conn.execute(
            "SELECT COUNT(*) FROM sprint_tasks WHERE week=?", (week,)
        ).fetchone()[0]
        if existing:
            continue
        path = root / "weeks" / f"week-{week:02d}" / "README.md"
        for order, (label, completed) in enumerate(checkboxes(path), start=1):
            conn.execute(
                """INSERT OR IGNORE INTO sprint_tasks
                   (week,sort_order,label,completed) VALUES(?,?,?,?)""",
                (week, order, label, completed),
            )
            sprint_count += 1

    for project_id, dirname in PROJECT_DIRS.items():
        existing = conn.execute(
            "SELECT COUNT(*) FROM project_tasks WHERE project_id=?", (project_id,)
        ).fetchone()[0]
        if existing:
            continue
        path = root / "projects" / dirname / "TASKS.md"
        for order, (label, completed) in enumerate(checkboxes(path), start=1):
            conn.execute(
                """INSERT OR IGNORE INTO project_tasks
                   (project_id,sort_order,stage,label,completed)
                   VALUES(?,?,?,?,?)""",
                (project_id, order, stage_for(label), label, completed),
            )
            project_count += 1

    updated_tasks = _update_duckdb_exercise_tasks(conn)
    # Applied Labs are now owned by the adaptive Applied track. Recreating all
    # 36 historical static sprint rows would immediately duplicate that track.
    applied_tasks = {"added": 0, "updated": 0}
    roadmap_cleanup = _clean_legacy_roadmap_tasks(conn)
    portfolio_guidance = _sync_portfolio_task_guidance(conn)
    evidence_cleanup = _clean_academy_evidence(conn)

    from career_app.services import task_workspace
    workspace_cleanup = (
        task_workspace.cleanup_external_learning_workspaces(
            conn
        )
    )

    conn.commit()
    return {
        "sprint_tasks": sprint_count,
        "project_tasks": project_count,
        "updated_tasks": updated_tasks,
        "applied_tasks_added": applied_tasks["added"],
        "applied_tasks_updated": applied_tasks["updated"],
        "external_workspaces_removed": (
            workspace_cleanup["removed"]
        ),
        "roadmap_tasks_archived": roadmap_cleanup["archived"],
        "roadmap_tasks_retained": roadmap_cleanup["retained"],
        "roadmap_tasks_updated": roadmap_cleanup["updated"],
        "portfolio_tasks_guided": portfolio_guidance["updated"],
        "portfolio_tasks_missing_guidance": portfolio_guidance["missing"],
        "academy_evidence_removed": (
            evidence_cleanup["academy_rows_removed"]
            + evidence_cleanup["main_rows_removed"]
        ),
        "academy_projects_consolidated": evidence_cleanup["projects_consolidated"],
    }
