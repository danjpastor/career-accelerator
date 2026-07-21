# Guided Task Workbench

Career Accelerator v10.14.0 turns task documents into readable, guided workspaces.

## Markdown views

The **Visual Guide** tab is selected when a task opens and renders the Markdown document for comfortable reading. The **Raw Markdown** tab exposes the editable source, with autosave and a refreshed preview.

Visual Guides now provide:

- Line-numbered boxes for fenced code blocks
- A visible language label such as SQL, Python, JSON, YAML, or Code
- High-contrast inline code and file paths
- Clearer URL styling
- Larger monospace text in Raw Markdown and path fields
- Tables, headings, lists, links, and blockquotes styled for the application theme

## Files and folders from a guide

Inline-code paths such as `sql/validation/`, `sql/validation/01_primary_key_checks.sql`, or `docs/relationship_validation.md` are detected when they use a supported project-file extension or end with `/`. The workbench can create selected paths or every missing path.

Safety rules:

- Paths must stay inside the repository.
- Existing files are never overwritten.
- Portfolio paths are created under the relevant project folder unless the guide explicitly uses a repository-root prefix.
- A nearby fenced SQL, Python, JSON, YAML, CSV, or text block can seed a new file.

## SQL interview tasks

DataLemur tasks open the exact local problem in SQL Companion. The SQL Companion workspace then provides **Open on DataLemur ↗**, which opens the exact official question page in the default browser.

A SQL task is complete only after a non-template query has been saved. Completion preserves the submission path and notes, marks the practice record complete, and advances the adaptive SQL track.
