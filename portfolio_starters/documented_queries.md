# {project_name} — Documented SQL Package

**Milestone:** {label}  
**Started:** {date}

## Recommended structure

```text
sql/
├── schema/
├── load/
├── cleaning/
├── validation/
└── analysis/
```

## Query index

| File | Purpose | Inputs | Output grain | Business question | Run order | Validation |
|---|---|---|---|---|---:|---|
|  |  |  |  |  |  |  |

## Final review

- [ ] Files use clear names.
- [ ] Queries are formatted and commented.
- [ ] CTEs and aliases describe business meaning.
- [ ] Assumptions and exclusions are visible.
- [ ] Each output maps to a business question.
- [ ] All files run from a clean setup.
- [ ] No scratch queries, secrets, or absolute local paths remain.
