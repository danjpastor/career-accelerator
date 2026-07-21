# {project_name} — Clean and Validate Data

**Milestone:** {label}  
**Started:** {date}

## 1. Profile before cleaning

Record for each table:

| Table | Rows | Duplicate keys | Missing required values | Invalid types | Invalid categories/ranges | Date issues |
|---|---:|---:|---:|---:|---:|---:|
|  |  |  |  |  |  |  |

## 2. Cleaning rule register

| Issue | Detection rule | Cleaning action | Why this action is valid | Rows affected | Reversible? |
|---|---|---|---|---:|---|
|  |  |  |  |  | Yes / No |

## 3. Required outputs

- Preserve original files under `data/raw/`.
- Put intermediate files under `data/staging/`.
- Put final analysis-ready files under `data/processed/`.
- Save reproducible code in SQL or Python rather than editing cells manually.

## 4. Validate after cleaning

| Check | Before | After | Expected | Pass? | Notes |
|---|---:|---:|---:|---|---|
| Row count |  |  |  |  |  |
| Unique primary keys |  |  |  |  |  |
| Required values present |  |  |  |  |  |
| Valid relationships |  |  |  |  |  |

## Completion checklist

- [ ] Every transformation is documented.
- [ ] Raw files remain unchanged.
- [ ] Processed files can be recreated from code.
- [ ] Before-and-after validation is saved.
- [ ] Unresolved issues are listed explicitly.
