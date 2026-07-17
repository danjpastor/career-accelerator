# Automatic Task Workspace Artifacts

Career Accelerator automatically links outputs that it already manages.

## DataLemur SQL solutions

Creating or opening a DataLemur solution immediately links the original
`.sql` file to the matching task workspace. Completing the problem
reconciles the same path before the adaptive SQL task advances.

Existing historical SQL workspaces are repaired when opened. The resolver
checks the saved `sql_practice.solution_path` first and then the standard
`resources/sql/datalemur/<problem-slug>.sql` location.

The file is referenced in place; it is never copied or duplicated.

## Other managed outputs

DuckDB SQL submissions and Applied Lab submissions are also shown as
automatic artifacts when their workspaces are opened.

Automatic artifacts are labeled **Automatic** and cannot be unlinked
manually. Removing or moving the source through its owning workflow is the
correct way to change the reference.

## External learning

Google Certificate and DataCamp activities remain visible in Learning,
adaptive scheduling, and Study Sessions, but they do not create or appear
in Task Workspaces.
