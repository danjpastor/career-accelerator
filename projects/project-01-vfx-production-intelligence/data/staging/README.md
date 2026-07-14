# Staging Data

Store standardized intermediate outputs here.

Typical staging work includes:

- trimming and normalizing identifiers
- parsing dates and numeric fields
- standardizing statuses, departments, and boolean values
- flagging duplicates and invalid foreign keys
- preserving rejected or quarantined records

Staging files should be reproducible from `data/raw/`.
