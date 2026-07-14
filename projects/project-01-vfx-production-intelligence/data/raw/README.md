# Raw Data — Preserve Unchanged

This directory contains the original source package.

- `vfx_production_intelligence_synthetic_raw.xlsx` is the master workbook.
- `csv/` contains the six operational tables for SQL, Python, or Power BI.

Do not correct values directly in this directory. Copy or load the files into
`data/staging/`, then create cleaned outputs under `data/processed/`.
