# {project_name} — Relationship Validation

**Milestone:** {label}  
**Started:** {date}

## What this task means

Before joining project tables, confirm that their keys and row relationships behave as expected. A query can run without errors and still produce incorrect totals when a key is duplicated, a child row points to a missing parent, or a join multiplies records.

The app prepares a project-specific DuckDB database and a guided Jupyter notebook when this task opens. Use **Open Notebook in VS Code** rather than creating setup scripts or disconnected SQL files yourself.

## What you will check

1. Primary-key candidates are unique.
2. Required foreign keys match a parent row.
3. Many-to-one joins preserve the child-row count.
4. Project-specific relationship rules remain consistent.

## How to work

- Review the table schemas and inferred relationships in the Visual Guide.
- Open the generated notebook in VS Code.
- Run the single collapsed setup cell once.
- Write the actual project SQL directly in the native `%%sql` cells.
- Inspect each result directly below its query.
- Replace the interpretation prompts with your own findings and decisions.
- Restart the kernel and run the notebook from top to bottom before finishing.

The Visual Guide contains the table schemas and relationships. The notebook stays minimal and does not provide the finished validation queries.

## Definition of done

- [ ] Every declared primary-key candidate was checked for duplicates.
- [ ] Every required relationship was checked for missing parent records.
- [ ] Join row counts were compared for relationships used in the analysis.
- [ ] Any project-specific consistency checks were considered.
- [ ] Every result has a written interpretation.
- [ ] The final conclusion states whether the relationships are safe to use.
- [ ] The notebook runs from top to bottom in a fresh kernel.
