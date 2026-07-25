# Clients Cleaning Summary

- **Source:** `data/raw/csv/raw_clients.csv`
- **Processed output:** `data/processed/csv/clients.csv`
- **Expected primary key:** `client_id`
- **Last updated:** 2026-07-25T14:43:32

## Decisions and remaining exceptions

The Clients table was cleaned by trimming and standardizing client identifiers, organization names, category labels, regions, contract tiers, active-status values, and account-manager names according to the completed Data Dictionary. Exact duplicate records for CL-007 and CL-012 were removed, reducing the table from 14 export rows to 12 unique client records. N. America was standardized to North America, affirmative active-status variants were mapped to Y, valid numeric revision-tendency and SLA values were preserved, and blank optional notes were converted to null without imputation. The clean client table contains a complete and unique primary key. The remaining client-related exception is the project record referencing CL-999; because no matching client exists, that issue will be resolved or quarantined during the Projects cleaning stage rather than inventing a client record.

## Latest validation

- Blocking issues: 0
- Warnings: 0
- Structural changes reviewed: 2
- Processed rows: 12
