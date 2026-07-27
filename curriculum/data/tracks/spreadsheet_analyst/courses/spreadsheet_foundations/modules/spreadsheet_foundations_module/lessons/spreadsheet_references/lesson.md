# Cell References, Sorting & Filtering

Create calculated columns with relative references, then use an absolute reference for a shared business assumption.

## Learn

Relative references change with the row. Absolute references use dollar signs to keep a cell fixed. For example, `=K2*(1+'Lookup Tables'!$B$2)` changes K2 as it fills down but always uses the tax rate in B2.

## Try It

On Orders, add a new column named Revenue in K1. In K2, calculate Units × Unit Price × (1 − Discount), then fill the formula through K37.

## Practice

Create Adjusted Revenue in column L using each row’s Revenue and the shared tax rate in 'Lookup Tables'!$B$2. Fill the formula through row 37. Then filter Region to West and sort Revenue from largest to smallest. Enter the Order ID at the top of the filtered list in Check Your Work.

## Check Your Work

Complete the task in the continuing linked Google Sheet. Wait until Google Sheets finishes saving, return to Accelerator Academy, and select **Check My Work**. Career Accelerator downloads the latest shared workbook and runs the lesson validator automatically.
