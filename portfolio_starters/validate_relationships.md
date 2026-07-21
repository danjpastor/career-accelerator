# {project_name} — Relationship Validation

**Milestone:** {label}  
**Started:** {date}

## What this task means

Before joining project tables, confirm that their keys and row relationships behave as expected. A query can run without errors and still produce incorrect totals when a key is duplicated, a child row points to a missing parent, or a join multiplies records.

The app prepares a project-specific DuckDB database and a guided SQL starter when this task opens. Use **Open Starter in VS Code** rather than creating setup scripts yourself.

## What you will check

1. Primary-key candidates are unique.
2. Required foreign keys match a parent row.
3. Many-to-one joins preserve the child-row count.
4. Project-specific relationship rules remain consistent.

## How to work

- Review the table schemas and inferred relationships in the Visual Guide.
- Open the generated starter SQL in VS Code.
- Write the actual project queries in the blank TODO sections.
- Run statements with the DuckDB extension already configured in the generated workspace.
- Record results and conclusions in the generated findings document.

The starter contains only small placeholder syntax examples. It does not provide the finished validation queries.

## Definition of done

- [ ] Every declared primary-key candidate was checked for duplicates.
- [ ] Every required relationship was checked for missing parent records.
- [ ] Join row counts were compared for relationships used in the analysis.
- [ ] Any project-specific consistency checks were added.
- [ ] Exceptions and decisions were documented.
- [ ] The findings document states whether the relationships are safe to use.
