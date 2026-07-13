# Draft Data Dictionary

| Field | Table | Description |
|---|---|---|
| shot_id | Fact_Shots | Unique shot identifier |
| project_id | Fact_Shots | Project foreign key |
| artist_id | Fact_Shots | Artist foreign key |
| department_id | Fact_Shots | Department foreign key |
| assigned_date | Fact_Shots | Assignment date |
| start_date | Fact_Shots | Work start date |
| deadline | Fact_Shots | Required delivery date |
| delivery_date | Fact_Shots | Actual delivery date |
| estimated_hours | Fact_Shots | Planned hours |
| actual_hours | Fact_Shots | Actual hours |
| revision_count | Fact_Shots | Number of revisions |
| priority | Fact_Shots | Production priority |
| status | Fact_Shots | Current or final status |
