# Accelerator Academy

Accelerator Academy is Career Accelerator's built-in, program-neutral learning platform. The shared engine remains independent of any career program; program names, pathways, course content, datasets, skills, prerequisites, assessment rules, and evidence metadata are supplied through external curriculum packages under `curriculum/`.

## User-facing hierarchy

```text
Accelerator Academy
├── Learning Paths
├── Courses
├── Practice
├── Skills Lab
├── Assessments
└── Demonstrated Evidence
```

## Experience standard

Academy uses the same visual and interaction language as Learning → Exercises and Applied Labs:

- floating midnight-navy cards and the shared purple/magenta palette;
- fixed outer workspaces with scrolling delegated to lesson, activity, list, editor, and result regions;
- responsive horizontal/vertical split layouts;
- shared `CoursePageWidget`, `SqlCodeEditor`, `FeedbackLabel`, result-table styling, buttons, dropdowns, and status treatments;
- lesson navigation and activity progress on the left;
- Learn and Practice panels in the primary workspace;
- Applied Lab-style business briefs, submissions, rubrics, findings, and validation for Skills Lab work.

A curriculum renderer may not introduce program-specific naming or provider-specific behavior into these generic components.

## Phase 2A engine

The generic engine lives in `application/career_app/academy/` and supplies:

- immutable program, path, track, course, module, lesson, activity, assessment, Skills Lab, dataset, and progress models;
- safe YAML loading with identifier validation, duplicate detection, unknown-skill validation, package-boundary checks, and deterministic content hashes;
- additive SQLite persistence for packages, enrollments, four-state lesson progress, activity attempts, assessments, evidence, submissions, and provider-neutral external learning history;
- prerequisite-aware recommendations for instruction, guided practice, independent mastery, assessments, and Skills Labs;
- trusted validators, beginning with recognition and isolated read-only DuckDB query validation;
- projection of strong Academy work into existing Demonstrated Evidence and skill-inventory surfaces;
- one active Academy action routed through the existing adaptive planner.

The four lesson states are `Not Started`, `Learning`, `Practiced`, and `Mastered`. Opening content can only produce `Learning`. Declared guided requirements produce `Practiced`. `Mastered` requires all current independent mastery requirements to pass without solution assistance on the successful attempt.

## Curriculum package layout

```text
curriculum/
└── data/
    ├── program.yaml
    ├── skills.yaml
    ├── datasets/
    │   ├── datasets.yaml
    │   └── *.csv
    ├── paths/
    │   └── <path_id>/path.yaml
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

Package references may resolve only inside their curriculum package. Python code is never executed from curriculum folders. Trusted validators remain in `application/career_app/academy/validators/`; content packages provide declarative validation settings.

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

A future edition can provide a different package without changing the engine, planner adapter, progress repository, validators, or Academy layouts.

## Permanent lesson contract

Each lesson declares stable identifiers, description, estimated time, objectives, prerequisites, skills taught, original Markdown instruction, key takeaways, activities, practice/mastery requirements, and passing rules.

Each activity may declare:

- recognition, guided, independent, debugging, transfer, or mastery type;
- scenario and business introduction;
- available table and task;
- explicit requirements and expected output;
- skills practiced and estimated time;
- starter work, progressive hints, solution, and validator configuration;
- post-completion explanation and common-error guidance;
- practice, mastery, and evidence eligibility.

Worked examples must differ from paired practice in dataset or scenario, business question, output requirement, and final answer. High-level interactive-learning patterns may inform pacing, but Academy wording, examples, datasets, exercises, solutions, sequence, and teaching material must remain original.

## Content versioning

`schema_version` describes the package format. `content_version` describes a curriculum release. Package hashes are stored in `academy_packages`. Stable lesson and activity IDs preserve compatible work. When a new content version changes current requirements, the reconciliation step preserves answers and passed activities but recalculates the lesson state against the new contract. This prevents old mastery from bypassing newly required independent work.

## Query Foundations v1.1 pilot

The production pilot contains:

- five comprehensive lessons;
- 26 original lesson activities using all approved activity types;
- approximately 190 minutes of lesson instruction and practice;
- one seven-question, 80%-passing checkpoint;
- one 60-minute Customer Support Queue Analysis Skills Lab;
- prerequisite-aware adaptive recommendations;
- saved SQL and written-findings artifacts;
- automatic Demonstrated Evidence and skill-state integration.

DataCamp remains unchanged in Phase 2A and 2B. Provider-history mapping and replacement of required SQL quotas belong to Phase 2C.

## Adding another program edition

1. Create a top-level curriculum package.
2. Define brand and learning labels in `program.yaml`.
3. Define a stable skill graph.
4. Add paths, tracks, courses, modules, lessons, assessments, datasets, and Skills Labs.
5. Use an existing trusted runtime or add a program-neutral validator to the engine.
6. Run package, official-solution, progress, prerequisite, UI-construction, and installer tests before distribution.

Do not place career-specific course names, learner nouns, or provider names inside the generic engine.
