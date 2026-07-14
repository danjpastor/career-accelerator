# VFX Production Intelligence Dataset Setup

## What is supplied

The files under `data/raw/` are the original synthetic source data for this
portfolio project. Preserve them unchanged.

The files under `docs/source_brief/` are supplied reference material. They may
be used to understand the intended business context, expected fields, candidate
KPIs, and known issue categories. They are not the final project documentation.

## What you should author

Create your own work under:

- `data/staging/`
- `data/processed/`
- `docs/analysis/`
- `sql/schema/`
- `sql/cleaning/`
- `sql/validation/`
- `sql/analysis/`
- `notebooks/`
- `power-bi/`
- `outputs/`

Your final portfolio should contain your own profiling, cleaning rules,
validation logic, KPI definitions, SQL, model design, dashboard, findings,
recommendations, and project narrative.

## Recommended workflow

```text
data/raw
    ↓
data/staging
    ↓
data/processed
    ↓
SQL analysis and validation
    ↓
Power BI model and dashboard
    ↓
documented findings and recommendations
```

## Portfolio disclosure

A transparent description is:

> This project uses a synthetic VFX production dataset generated to simulate
> production-tracking, staffing, timesheet, and review-system exports. I
> independently completed the profiling, cleaning, validation, KPI methodology,
> SQL analysis, data modeling, dashboard development, interpretation, and final
> documentation.
