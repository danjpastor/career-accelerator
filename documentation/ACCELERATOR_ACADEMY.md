# Accelerator Academy

Accelerator Academy is Career Accelerator's built-in, program-neutral learning platform. The engine remains independent of any career program; program names, pathways, curriculum, datasets, skills, prerequisites, assessments, projects, and evidence metadata are supplied through external packages under `curriculum/`.

## Learner-facing experience

Academy presents one coherent learning path:

```text
Resume Learning
    ↓
Focused concept + immediate action
    ↓
Run, choose, complete, debug, or apply
    ↓
Validation and explanation
    ↓
Continue to the next step
    ↓
Course checkpoint
    ↓
Applied project
    ↓
Demonstrated Evidence
```

Courses, modules, practice, assessments, Skills Labs, and evidence remain internal curriculum types. They are not separate learner destinations. The Academy page contains:

- a persistent roadmap showing the ordered journey;
- collapsible course headers, with the active course expanded and future courses collapsed by default;
- one recommended current step;
- Back and Continue navigation;
- prerequisite and sequential locks;
- one interactive lesson player;
- checkpoint questions integrated into the roadmap;
- an applied project integrated as the final course milestone.

Every lesson step must contain an interactive action. Passive reading-only steps are not permitted.

Learner-facing copy should sound direct, supportive, and conversational. Interface text should explain the next action in plain language—for example, “Complete the lesson to move on!”—instead of describing internal state-machine behavior.

## Experience standard

Academy uses the same visual and interaction language as Learning → Exercises and Applied Labs:

- floating midnight-navy cards and the shared purple/magenta palette;
- transparent explanatory text and callouts that sit naturally on the parent card instead of adding unnecessary nested backdrops;
- fixed outer workspaces with scrolling delegated to cards, editors, lists, and results;
- responsive horizontal and vertical split layouts;
- shared `CoursePageWidget`, `SqlCodeEditor`, `FeedbackLabel`, result tables, buttons, and status treatments;
- focused concept instruction beside the active interaction;
- business context, available data, requirements, expected output, hints, validation, and post-completion explanation;
- Applied Lab-style project briefs, findings, validation, artifacts, and evidence.

## Phase 2A engine

The generic engine lives in `application/career_app/academy/` and supplies:

- immutable program, path, track, course, module, lesson, activity, assessment, project, dataset, and progress models;
- safe YAML loading with identifier validation, duplicate detection, unknown-skill validation, package-boundary checks, and deterministic content hashes;
- additive SQLite persistence for packages, enrollments, lesson/activity progress, assessment drafts and attempts, evidence, submissions, and provider-neutral external learning history;
- prerequisite-aware and sequence-aware recommendations;
- trusted declarative validators, beginning with recognition and isolated read-only DuckDB validation;
- projection of strong work into the existing Demonstrated Evidence and skill-inventory surfaces;
- one current Academy action routed through the adaptive planner.

The four lesson states remain `Not Started`, `Learning`, `Practiced`, and `Mastered`:

- **Learning:** the lesson has been opened or a step has begun.
- **Practiced:** every required non-mastery interactive step has passed.
- **Mastered:** the practice sequence and designated mastery step have passed, with the mastery attempt completed without viewing the full solution.

## Curriculum package layout

```text
curriculum/
└── data/
    ├── program.yaml
    ├── skills.yaml
    ├── datasets/
    ├── paths/
    └── tracks/
        └── <track_id>/
            ├── track.yaml
            └── courses/
                └── <course_id>/
                    ├── course.yaml
                    ├── modules/
                    ├── assessments/
                    └── skills_labs/
```

Package references may resolve only inside their curriculum package. Curriculum folders cannot execute Python. Trusted validators remain under `application/career_app/academy/validators/`.

## Program-neutral configuration

```yaml
brand:
  family_name: Career Accelerator
  program_name: Data
  application_name: Data Career Accelerator

learning:
  system_name: Accelerator Academy
  pathway_name: Data Analytics Pathway
  learner_noun: analyst
  evidence_label: Demonstrated Evidence
  skills_lab_label: Skills Lab
```

A future edition can provide different configuration and content without changing the engine, planner adapter, progress repository, validators, or generic Academy layouts.

## Interactive step contract

Each lesson activity is rendered as one sequential learning step and may declare:

```yaml
instruction:
  title: Begin with the unit of analysis
  objective: Identify what one row represents before analysis.
  action_label: Identify the grain
  body: |
    Original concept instruction, examples, common mistakes, and context.

required_for_completion: true
presentation:
  scenario: Support operations orientation
  introduction: Why the action matters in this scenario.
  task: The exact interactive action.
  requirements:
    - Explicit completion requirement
  expected_output: A verifiable output description.
  skills_practiced:
    - table grain
```

Supported step interactions currently include recognition, guided SQL, independent SQL, debugging, transfer, and mastery. Future runtimes can add Python, command-line, configuration, or artifact interactions while preserving the same sequential contract.

Worked examples must differ from their paired action in dataset or scenario, business question, output requirement, and final answer. High-level interactive-learning principles may inform pacing, but wording, examples, datasets, questions, solutions, sequence, and teaching material must remain original.


## Unified workspace contract

The active learner screen uses two functional areas:

- **Lesson & Practice:** focused instruction, worked examples, scenario, task, requirements, expected output, skills, and the exact schema for every referenced table.
- **Editor & Output:** only the active SQL editor or answer control, validation feedback, explanation, and output results.

Run Query, Check Answer, Show Hint, View Solution, Back, and Continue share one workflow row. The footer is divided into two responsive regions synchronized to the live lesson/editor splitter: Back and the completion requirement remain on the lesson side, while the active interaction controls and Continue remain on the editor side. SQL steps display a vertical editor/output splitter; recognition steps replace that workspace with one uninterrupted answer surface so no empty editor/output divider remains. Track and course labels are supplied by curriculum configuration so additional SQL, Python, visualization, statistics, or communication courses can be added without changing the generic UI. The path-progress area displays course and lesson milestone circles connected by status-aware progress rails. Lesson headers in the pathway card use distinct tints for current, complete, in-progress, available, and locked states. Roadmap state is loaded in bulk and the immutable journey structure is cached, so expanding courses and moving between steps does not perform one database query per curriculum node.

## SQL table-schema requirement

Every SQL activity must declare the table or tables used by the question:

```yaml
presentation:
  table: support_tickets
  # or
  tables:
    - orders
    - customers
```

The package loader rejects missing or unknown table references. Academy loads the same CSV data through DuckDB that the query runtime uses and displays DuckDB's inferred column names and data types before the learner writes a query. This requirement applies to lesson steps, checkpoint questions, and applied projects.

## Sequence and gating rules

1. A lesson must satisfy its declared skill prerequisites.
2. Within a lesson, every earlier required step must pass before a later step unlocks.
3. Continue remains disabled until the current action passes.
4. Viewing a solution does not overwrite learner work.
5. A solution-assisted mastery attempt must be passed again independently.
6. The checkpoint unlocks only after required lesson skills are mastered.
7. The applied project unlocks only after the checkpoint passes.
8. Validated projects, capstones, and Skills Labs create Demonstrated Evidence automatically; routine lesson work remains in mastery progress.


## Demonstrated Evidence policy

Routine instruction, recognition checks, guided practice, independent lesson steps, and lesson mastery remain part of Academy progress and skill mastery. They do not create employer-facing Demonstrated Evidence records.

Automatic Academy evidence is reserved for validated substantial work:

- integrated projects;
- capstones;
- Skills Labs;
- equivalent applied submissions explicitly marked as evidence-producing.

A completed project may demonstrate several skills internally, but Job Readiness displays one consolidated evidence entry for the project rather than one entry for every lesson or skill.

## Content versioning

`schema_version` describes the package format. `content_version` describes a curriculum release. Stable lesson and activity IDs preserve compatible work. When requirements change, reconciliation preserves answers and passed activities but recalculates lesson state against the current contract.

## Built-in curriculum v1.5

The SQL track now uses this seven-course sequence:

1. **Introduction to SQL**
   - Introduction to SQL
2. **Intermediate SQL**
   - Data Aggregation
   - Data Transformation
   - Data Filtering
   - Conditional Operations
3. **Joining Data in SQL**
   - Combining Data Vertically
   - Combining Data Horizontally
4. **Data Manipulation in SQL**
   - We'll Take the CASE
   - Short and Simple Subqueries
   - Correlated Queries, Nested Queries, and Common Table Expressions
   - Window Functions
5. **PostgreSQL Summary Stats and Window Functions**
   - Introduction to Window Functions
   - Fetching, Ranking, and Paging
   - Aggregate Window Functions and Frames
   - Beyond Window Functions
6. **Functions for Manipulating Data in PostgreSQL**
   - Overview of Common Data Types
   - Working with DATE/TIME Functions and Operators
   - Parsing and Manipulating Text
   - Full-Text Search and PostgreSQL Extensions
7. **Database Design**
   - Processing, Storing, and Organizing Data
   - Database Schemas and Normalization
   - Database Views
   - Database Management

The SQL sequence contains 35 lessons, seven course checkpoints, and two integrated bonus projects:

- **Bonus Project — Analyzing Students' Mental Health** after Intermediate SQL;
- **Bonus Project — Impact Analysis of GoodThought NGO Initiatives** after Database Design.

The public course and chapter taxonomy is used only as a coverage and organization benchmark. Accelerator Academy supplies original lesson explanations, examples, datasets, questions, SQL, validators, solutions, project briefs, and evidence requirements. Existing compatible learner work is preserved through stable lesson and activity identifiers and content-version reconciliation.

The complete built-in Academy path now contains 193 interactive lesson, checkpoint, and project nodes across SQL, Power BI, Python, and pandas. DataCamp remains excluded from active recommendations and weekly requirements; historical completions remain preserved as External Learning History.
