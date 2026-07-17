# Career Accelerator Exercise Pack Format v1 — v10 authoring rules


> **Authoring documentation:** Start with `AUTHORING_GUIDE.md`, use `STYLE_GUIDE.md` for course presentation, and complete `QUALITY_CHECKLIST.md` before release. A copyable starter is available in `templates/standard-pack-template/`.

Exercise Packs are optional, portable learning modules installed from either a folder or a `.zip` file. They do not become required roadmap tasks. The app validates a pack, copies it into `exercise_packs/installed/<pack_id>/`, and stores user progress separately in the Career Accelerator SQLite database.

## Install a pack

1. Open **Learning → Exercises**.
2. Open the **⋮ Manage Packs** menu in the Exercises toolbar.
3. Choose **Install Exercise Pack…** for a `.zip`, or **Install Folder…** for an unpacked folder.
4. Select the pack. After validation, it appears immediately in the pack selector and learning path.

A newer pack with the same `pack_id` replaces its content while preserving saved SQL, notes, and completion progress.

## Required folder structure

```text
my-exercise-pack/
├── manifest.json
├── README.md                         # optional but recommended
├── lessons/                          # optional
│   └── 01-concept-introduction.md
├── exercises/
│   └── 01-first-exercise.json
├── datasets/
│   └── example.csv
└── solutions/
    └── 01-first-exercise.sql
```

The selected folder—or the single top-level folder inside a `.zip`—must contain exactly one `manifest.json`.

## `manifest.json`

```json
{
  "schema_version": 1,
  "pack_id": "sql-example-pack",
  "title": "SQL Example Pack",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "What the learner will understand and practice.",
  "difficulty": "Very Beginner → Intermediate",
  "estimated_minutes": 120,
  "concepts": ["SELECT", "WHERE", "subqueries"],
  "prerequisites": ["Basic SELECT queries"],
  "trigger_concepts": ["sql_subqueries"],
  "trigger_keywords": ["subquery", "nested query"],
  "suggestion_rules": [
    {
      "concept_any": ["sql_subqueries"],
      "category_any": ["SQL", "Learning"],
      "score": 140,
      "reason": "A current task uses concepts practiced by this pack."
    }
  ],
  "lessons": [
    {
      "id": "concept-introduction",
      "title": "Concept Introduction",
      "subtitle": "Start with one clear mental model",
      "file": "lessons/01-concept-introduction.md"
    }
  ],
  "exercises": [
    {
      "id": "first-exercise",
      "title": "First Exercise",
      "file": "exercises/01-first-exercise.json",
      "lesson_id": "concept-introduction",
      "question_number": 1,
      "show_starter_sql": true
    }
  ]
}
```

### Required manifest fields

| Field | Rule |
|---|---|
| `schema_version` | Must be `1`. |
| `pack_id` | Stable lowercase identifier using words and hyphens. Never change this when publishing an update. |
| `title` | User-facing pack title. |
| `version` | Pack version string. |
| `description` | Plain-language explanation of the pack. |
| `exercises` | At least one question entry. Each entry needs `id`, `title`, `file`, `lesson_id`, and `question_number`. Every lesson must have at least one associated question. |

Lesson and exercise IDs must be unique across the whole pack. Referenced paths must stay inside the pack folder.

### Lesson-to-question rules in v10

- Every lesson must have at least one associated practice question.
- `lesson_id` must exactly match a manifest lesson ID.
- `question_number` controls the order shown within that lesson and should begin at `1`.
- `show_starter_sql` controls whether the authored `starter_sql` appears for a brand-new answer. When false, the editor opens empty.
- A learner's previously saved SQL always takes precedence over the starter template.
- A starter template may contain comments, requested column placeholders, an empty CTE, or a required table name, but it must not contain the solution logic, a lesson example copied into the editor, or a nearly completed answer.
- Lesson Markdown code examples are instructional only and are never copied into Practice automatically.

## Dashboard suggestion rules

Suggestions are recalculated from live, incomplete tasks in the active week every time the Dashboard refreshes. They are not stored in or limited by the stable daily task snapshot.

A pack should prefer canonical `trigger_concepts`, may retain `trigger_keywords` as a text fallback, and can define one or more `suggestion_rules`. Task concepts are refreshed by the full-catalog audit described in `TASK_TAG_AUDIT.md`.

| Rule field | Meaning |
|---|---|
| `trigger_concepts` | Top-level pack concepts. A match receives higher priority than title-keyword matching. |
| `concept_any` | Match when any listed canonical concept exists on an incomplete current-week task. |
| `concept_all` | Match when all listed canonical concepts exist on the same incomplete current-week task. |
| `task_keyword_any` | Backward-compatible fallback matching against task text and metadata. |
| `category_any` | Limit matching to task categories such as `SQL` or `Learning`. |
| `google_course_any` | Match one of the listed active Google course numbers. |
| `google_module_any` | Match one of the listed active Google module numbers. |
| `score` | Relative priority when multiple packs match. Higher wins. |
| `reason` | Tooltip text explaining why the pack was suggested. |

Suggestions remain optional. A completed pack is no longer recommended.

## Exercise JSON

```json
{
  "id": "first-exercise",
  "lesson_id": "concept-introduction",
  "question_number": 1,
  "show_starter_sql": true,
  "title": "First Exercise",
  "stage": "Stage 1 • First principle",
  "subtitle": "Stage 1 • Build the first mental model",
  "difficulty": "Very Beginner",
  "estimated_minutes": 10,
  "concepts": ["AVG", "scalar result"],
  "learning_objective": "The specific skill the learner should demonstrate.",
  "recommended_lesson": "Lesson 1: Concept Introduction",
  "why": "Why an analyst would use this pattern.",
  "prompt": "The exact question the learner must answer.",
  "expected_result": "The expected columns, row count, and ordering without giving away the SQL.",
  "build_steps": ["First small step.", "Second small step."],
  "explanation": "A small mental model without giving away the answer.",
  "common_mistakes": ["One likely mistake and why it is wrong."],
  "reflection_questions": ["A question that checks conceptual understanding."],
  "stretch_goal": "An optional extension after the required answer works.",
  "starter_sql": "SELECT\n    -- finish the query\nFROM example;",
  "hints": [
    "First hint.",
    "More specific second hint."
  ],
  "takeaways": [
    "One important idea to remember."
  ],
  "datasets": [
    {
      "table": "example",
      "file": "datasets/example.csv"
    }
  ],
  "solution_file": "solutions/01-first-exercise.sql",
  "solution_explanation": "Why the official solution works.",
  "solution_walkthrough": ["Explain the first query stage.", "Explain the outer use."],
  "validation": {
    "mode": "result",
    "ordered": false,
    "required_keywords": ["avg"],
    "min_select_count": 1
  }
}
```

Required fields are `id`, `lesson_id`, `question_number`, `title`, `prompt`, `starter_sql`, `datasets`, and `solution_file`. `show_starter_sql` is strongly recommended and defaults to true for compatible packs. Dataset table and CSV column names must be valid SQL identifiers containing letters, numbers, and underscores.

### Starting-template policy

The SQL editor is a learner workspace, not an answer preview. For a new question it may load only the authored `starter_sql`, and that template must leave the taught reasoning for the learner to complete. Do not paste the official solution, the lesson's example query, completed joins, completed predicates, completed aggregation logic, or hard-coded expected rows into `starter_sql`.

A safe default is:

```sql
-- Write your answer below.
-- Use the task, expected output, and dataset details above.

SELECT
    -- requested columns
FROM table_name;
```

Set `show_starter_sql` to false when even that amount of scaffolding would reveal too much. Opening View Solution never replaces learner SQL; copying a solution requires a separate explicit action.

### Recommended instructional fields

These fields are optional for compatibility, but polished packs should use them consistently. The Exercises UI renders them as a structured learning card and solution walkthrough.

| Field | Purpose |
|---|---|
| `stage` | Shows where the exercise sits in the learning progression and in status text. |
| `subtitle` | Supplies the calm outlined label directly beneath the lesson or exercise title. Keep it brief, descriptive, and sentence case. |
| `learning_objective` | States the single skill the learner should demonstrate. |
| `recommended_lesson` | Points to prerequisite reading within the pack. |
| `expected_result` | Describes output columns, row count, and ordering without revealing SQL. |
| `build_steps` | Breaks construction into small, testable stages. |
| `common_mistakes` | Warns about likely logical or result-shape errors. |
| `reflection_questions` | Checks whether the learner can explain the query, not merely run it. |
| `stretch_goal` | Provides optional extension work without blocking completion. |
| `solution_explanation` | Explains the overall reasoning behind the official query. |
| `solution_walkthrough` | Explains the query stage by stage in the solution dialog. |

## Lesson and course-material formatting

Lesson files use a constrained Markdown subset that is rendered consistently across platforms. The Exercises UI supplies the course-site presentation automatically using native Qt course components rather than a single rich-text document. This gives pack authors consistent responsive spacing, code controls, tables, callouts, breadcrumbs, bookmarks, and lesson navigation.

- Start each lesson with one `#` title. The UI renders it beneath a compact content-type pill, followed by the optional manifest `subtitle` label and a quiet divider.
- Use `##` for major sections and `###` for smaller checkpoints. The UI adds hierarchy and divider lines.
- Put every multi-line code example in a fenced block with a language label. SQL examples should use ` ```sql ` so they receive an **SQL** header, line numbers, syntax highlighting, and a Copy button.
- Put short SQL keywords, expressions, aliases, table names, and column names in backticks. They render as inline code chips.
- Use Markdown tables for schemas, comparisons, and sample outputs. The UI supplies header bands, alternating rows, alignment, and subtle separators.
- Use blockquotes for learning goals, tasks, warnings, and important reminders. They render as accented callout cards.
- Use `---` when an intentional full-width divider is useful; section headings already include their own divider.

### Optional two-column lesson rows

Use the portable `:::columns` directive when two related pieces of course content should appear side by side, such as learning goals beside a code example or a result table beside a key-idea callout. Each column may contain the same constrained Markdown used elsewhere.

````markdown
:::columns
:::column
> **Learning Goals:**
> ✓ Identify the inner query.
> ✓ Predict its result shape.
:::column
```sql
SELECT AVG(salary)
FROM employees;
```
:::
````

Keep two-column rows focused and short. On narrower workspaces, avoid wide tables with many columns.

Example:

````markdown
# One-Value Subqueries

> **Learning goal:** Use one returned value as a benchmark.

## Example

```sql
SELECT employee_name, salary
FROM employees
WHERE salary > (
    SELECT AVG(salary)
    FROM employees
);
```

## Result shape

| Inner result | Outer use |
|---|---|
| One value | Compare with `>`, `<`, or `=` |
````

Avoid ASCII-art tables and unlabelled code fences. The renderer can recognize common SQL terms automatically, but explicit backticks remain the most reliable and intentional authoring style.

## SQL execution and validation

Format v1 SQL exercises run in an isolated, in-memory SQLite database created fresh for each attempt. Every listed CSV becomes a table using its declared `table` name.

Only one read-only `SELECT` or `WITH` statement may run. Statements that modify data, attach databases, load extensions, create objects, or access the filesystem are rejected.

When **Check Answer** is selected:

1. The learner query runs against a fresh database.
2. The solution query runs against a separate fresh database with the same CSV data.
3. Selected column names and returned values are compared.
4. Row order is checked only when `validation.ordered` is `true`.
5. Optional learning-pattern rules confirm that the learner used the concept being practiced.

Supported validation fields:

| Field | Meaning |
|---|---|
| `ordered` | Require the same row order as the official solution. |
| `required_keywords` | Require every listed SQL keyword or phrase. Whitespace between phrase words is flexible. |
| `required_any_keywords` | Require at least one listed SQL keyword or phrase. |
| `forbidden_keywords` | Reject listed patterns when an exercise intentionally practices another approach. |
| `min_select_count` | Require at least this many `SELECT` statements, which helps verify that a nested-query exercise was not solved with a flat alternative. |

Pattern rules supplement result validation; they do not replace it. Keep them limited to the specific concept being taught so valid learner variations remain accepted.

Solutions are available through **View Solution** in a separate walkthrough dialog. The learner's editor is not replaced unless **Copy to Editor** is chosen.

## Authoring guidelines

- Teach one new idea at a time.
- Start with an inspectable inner query before nesting it.
- Keep early datasets small enough to reason through manually.
- Explain the analytical reason for each pattern, not only its syntax.
- Make hints progressively more specific.
- Keep starter SQL incomplete but structurally helpful.
- Validate every official solution before publishing.
- Use a new `version` when changing pack content; retain the same `pack_id` so progress survives updates.

## Packaging a `.zip`

Either of these layouts is accepted:

```text
manifest.json
lessons/
exercises/
...
```

or:

```text
my-exercise-pack/
    manifest.json
    lessons/
    exercises/
    ...
```

Do not include multiple packs in one archive. Packs are limited to 250 files and 30 MB in Format v1.
