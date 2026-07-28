# Applied Lab 01: Build a guided Google Sheets sales summary

## Why you are doing this

You have completed two weeks of spreadsheet study. This lab gives you one small project where you can use the skills together without being expected to design a professional reporting system from scratch.

You will work with a 24-row order file and a four-row regional target file. The Google Sheets Analyst Studio in Career Accelerator breaks the work into four stages. Complete them in order.

## What you will practice

- Importing and formatting CSV data
- Relative and absolute cell references
- `IF`, `TEXT`, `TRIM`, and `PROPER`
- `COUNTIF`, `COUNTIFS`, `SUMIF`, and `SUMIFS`
- `IFERROR` and `VLOOKUP`
- A data-validation dropdown
- Sorting and filtering
- One pivot table and one chart
- Explaining a result in plain language

## What you will build

Create one Google Sheet with four tabs:

1. `Raw Orders`
2. `Targets`
3. `Analysis`
4. `Summary`

Career Accelerator stores only the shareable spreadsheet link. It does not connect to your Google account or read your sheet.

---

# Stage 1: Create the workbook and import the data

1. Open a blank Google Sheet.
2. Rename it `Northstar Sales Practice`.
3. Create the four tabs listed above.
4. Open the supplied dataset folder from the Studio.
5. Import `orders.csv` into `Raw Orders`.
6. Import `targets.csv` into `Targets`.
7. Freeze row 1 on both source tabs.
8. Format `order_date` as a date, `quantity` as a whole number, and `unit_price` as currency.

Check before continuing:

- `Raw Orders` contains 24 data rows and 24 unique order IDs.
- `Targets` contains four data rows.
- You have not edited or deleted any source row.

Save the Google Sheets link in the Studio and record Stage 1 evidence.

---

# Stage 2: Clean the fields and calculate sales

Create these headers in `Analysis!A1:M1`:

| Column | Header |
|---|---|
| A | order_id |
| B | order_date |
| C | month |
| D | raw_region |
| E | clean_region |
| F | product |
| G | status |
| H | quantity |
| I | unit_price |
| J | gross_sales |
| K | processing_fee |
| L | net_sales |
| M | quality_check |

Copy the matching source fields from `Raw Orders` into columns A, B, D, F, G, H, and I.

Enter these formulas in row 2:

**Month — C2**

```gs
=TEXT(B2,"yyyy-mm")
```

**Clean region — E2**

```gs
=PROPER(TRIM(D2))
```

On `Summary`, enter `Processing Fee Rate` in A2 and `2%` in B2.

**Gross sales — J2**

```gs
=IF(G2="Completed",H2*I2,0)
```

**Processing fee — K2**

```gs
=J2*Summary!$B$2
```

The dollar signs make `Summary!$B$2` an absolute reference, so the fee-rate cell stays fixed when the formula is copied.

**Net sales — L2**

```gs
=J2-K2
```

**Quality check — M2**

```gs
=IF(A2="","Missing order ID",IF(E2="","Missing region",IF(H2<=0,"Check quantity","OK")))
```

Copy C2, E2, and J2:M2 through row 25.

Check before continuing:

- The Analysis tab contains 24 rows and 24 unique order IDs.
- ` west ` and `east` are cleaned to `West` and `East`.
- Cancelled orders show zero gross sales and zero net sales.
- Every quality check says `OK`.
- Changing the 2% fee rate changes processing fees and net sales.

Try sorting by order date and filtering the status column to `Completed`, then clear the filter.

---

# Stage 3: Build the summary and pivot table

On `Summary`, create:

| Cell | Content |
|---|---|
| A2 | Processing Fee Rate |
| B2 | 2% |
| A4 | Selected Region |
| B4 | Region dropdown |
| A6 | Completed Orders |
| A7 | Gross Sales |
| A8 | Net Sales |
| A9 | Average Net Order Value |
| A10 | Regional Sales Target |

Create a dropdown in B4 containing:

- All
- East
- West
- South
- North

Use these formulas. Replace the descriptive cell names in the average formula with the actual KPI cells you use.

**Completed orders**

```gs
=IF(B4="All",COUNTIF(Analysis!G2:G25,"Completed"),COUNTIFS(Analysis!G2:G25,"Completed",Analysis!E2:E25,B4))
```

**Gross sales**

```gs
=IF(B4="All",SUMIF(Analysis!G2:G25,"Completed",Analysis!J2:J25),SUMIFS(Analysis!J2:J25,Analysis!G2:G25,"Completed",Analysis!E2:E25,B4))
```

**Net sales**

```gs
=IF(B4="All",SUMIF(Analysis!G2:G25,"Completed",Analysis!L2:L25),SUMIFS(Analysis!L2:L25,Analysis!G2:G25,"Completed",Analysis!E2:E25,B4))
```

**Average net order value**

```gs
=IFERROR(net_sales_cell/completed_orders_cell,0)
```

For example, if Completed Orders is B6 and Net Sales is B8:

```gs
=IFERROR(B8/B6,0)
```

**Regional target**

```gs
=IF(B4="All","—",IFERROR(VLOOKUP(B4,Targets!A2:B5,2,FALSE),"Not found"))
```

Now create a pivot table from `Analysis!A1:M25`:

- Rows: `clean_region`
- Columns: `month`
- Values: SUM of `gross_sales`

Create one column chart from the pivot table. Title it:

> Sales by Region and Month

Check the All-region values:

- Completed orders: **20**
- Gross sales: **$1,650.00**
- Net sales: **$1,617.00**
- Average net order value: **$80.85**

Test at least two region selections and confirm all KPI values change.

---

# Stage 4: Validate and explain one result

Check the pivot table:

- January gross sales: **$755.00**
- February gross sales: **$895.00**

Regional gross sales should be:

- South: **$470.00**
- East: **$455.00**
- North: **$390.00**
- West: **$335.00**

Write two or three sentences in the Studio. A strong response:

1. Identifies South as the highest-gross-sales region.
2. States the amount without exaggerating what it proves.
3. Names one useful follow-up question, such as whether product mix or order quantity explains the difference.

Example structure:

> South produced the highest gross sales at $470, slightly ahead of East at $455. This shows where sales were strongest in this small practice dataset, but it does not explain why. I would next compare product mix and average quantity by region.

Use your own wording.

## Completion requirements

- A valid shareable Google Sheets URL is saved.
- All four guided stages contain evidence and are marked complete.
- All five final-review items are checked.
- A two-to-three-sentence takeaway is saved.

This lab is coursework, not a portfolio project. Clear formulas, correct checkpoints, and understanding what you built matter more than elaborate design.
