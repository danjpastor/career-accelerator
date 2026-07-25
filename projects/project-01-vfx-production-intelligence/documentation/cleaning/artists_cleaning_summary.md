# Artists Cleaning Summary

- **Source:** `data/raw/csv/raw_artists.csv`
- **Processed output:** `data/processed/csv/artists.csv`
- **Expected primary key:** `artist_id`
- **Last updated:** 2026-07-25T14:38:13

## Decisions and remaining exceptions

The artists table was cleaned by standardizing text fields, email formatting, categorical values, dates, weekly capacity, and hourly cost data according to the completed Data Dictionary. Confirmed duplicate or superseded employee records were consolidated under a single canonical artist_id, with downstream references remapped before obsolete records were excluded; this included retaining ART-023 as Liam Young’s current Senior Lighting Artist record and ART-012 as Nico Patel’s confirmed Senior Paint Artist record. The incorrect Nico Patel email on ART-013 was corrected to Riley Allen’s company address. Valid null manager_id values were retained for artists without a direct manager, and no missing or questionable numeric values were replaced unless an approved business decision supported the correction. Remaining exceptions are limited to documented cases where organizational hierarchy or historical role changes cannot be proven from the source data alone; these records were preserved or flagged rather than altered without evidence.

## Latest validation

- Blocking issues: 0
- Warnings: 0
- Structural changes reviewed: 3
- Processed rows: 58
