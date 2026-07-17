# Task Concept Tag Audit

Career Accelerator recalculates canonical concept tags for **every stored task** whenever the Dashboard asks for an Exercise Pack recommendation. This audit is separate from the stable daily task snapshot, so a newly installed or newly relevant pack can be suggested immediately.

## Why tags are necessary

Task titles are often intentionally short. A label such as `Google Certificate: Course 5, Module 3` does not contain the words `subquery` or `join`, even though those concepts are part of the module. Exercise Packs therefore match stable concept IDs rather than depending only on visible title text.

Examples:

| Task | Canonical tags |
|---|---|
| Google Course 5, Module 3 | `analysis_foundations`, `sql_joins`, `sql_subqueries` |
| DataCamp: Short and Simple Subqueries | `sql_subqueries`, `sql_intermediate` |
| SQL Practice: Signup Activation Rate | `sql_aggregation`, `sql_joins` |
| DuckDB Exercise 07 | `sql_subqueries`, `sql_ctes`, `sql_intermediate` |
| Project task: Validate SQL findings | `sql_fundamentals`, `sql_joins`, `sql_validation` |

## Sources checked

The audit checks task information in descending order of reliability:

1. Exact Google course/module mappings
2. Exact verified DataCamp chapter mappings
3. Exact SQL Companion problem mappings
4. Exact DuckDB exercise mappings
5. Exact Applied Lab mappings
6. Exact portfolio milestone mappings
7. Canonical keyword and phrase aliases
8. Low-confidence track/category coverage tags

When the application’s current `tracks.py` and `roadmap.py` catalogs are importable, their live mappings extend or override the bundled fallback maps.

## Persistence and stale-tag cleanup

Tags are stored in `task_concept_tags` with:

- `task_id`
- canonical `concept`
- mapping `source`
- numeric `confidence`
- `updated_at`

The table is synchronized from the full `sprint_tasks` catalog. Tags for removed tasks are deleted, and all tags for a changed task are recalculated. This prevents a task that moved from Module 3 to Module 4, for example, from retaining an obsolete subquery tag.

## Pack matching

Pack manifests may declare:

```json
"trigger_concepts": ["sql_subqueries"]
```

Suggestion rules may also use:

```json
{
  "concept_any": ["sql_subqueries", "sql_ctes"],
  "category_any": ["SQL", "Learning"],
  "score": 140,
  "reason": "A current task uses multi-step SQL concepts practiced by this pack."
}
```

`concept_any` matches when any listed concept is present on an incomplete current-week task. `concept_all` may be used when all listed concepts must occur on the same task.

Title keywords remain supported as a backward-compatible fallback, but canonical concept matches receive higher recommendation priority.

## Programmatic audit report

The service exposes:

```python
report = exercise_packs.task_tag_audit(conn, state)
```

The report includes:

- total and tagged task counts
- untagged tasks
- tasks that received only low-confidence generic coverage
- concept occurrence counts
- each task with its concepts, source, and confidence

The bundled test suite builds a catalog of 129 representative Google, DataCamp, SQL, DuckDB, Applied Lab, and portfolio tasks and requires every one to receive at least one specific concept tag.
