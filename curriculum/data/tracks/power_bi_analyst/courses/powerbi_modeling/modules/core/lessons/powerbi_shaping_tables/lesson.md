# Shaping Tables

Shaping data means changing its structure so it is easier to analyze. In Power Query, you can rename fields, remove columns, split text, pivot or unpivot values, append similar tables, and merge related tables.

## Main idea

Shaping data means changing its structure so it is easier to analyze. In Power Query, you can rename fields, remove columns, split text, pivot or unpivot values, append similar tables, and merge related tables.

**Append** stacks rows from tables with the same kind of records. **Merge** matches columns between related tables. A left outer merge keeps every row from the first table and brings in matching values from the second. Always compare row counts before and after a merge so you can spot lost or duplicated records.

## Example

A company receives one monthly expense file per office. The analyst appends the files because every file contains the same columns. They later merge the combined expenses with an office lookup table to add region names. A left outer merge keeps every expense even when one office code is missing from the lookup.
