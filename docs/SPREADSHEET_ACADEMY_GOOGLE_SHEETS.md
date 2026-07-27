# Spreadsheet Academy Google Sheets workflow

Spreadsheet Academy uses one continuing **Northstar Operations Practice Workbook** throughout the spreadsheet pathway.

## One-time setup

1. Open a practical spreadsheet lesson.
2. Select **Get Starter Workbook** and save the `.xlsx` file.
3. Open Google Sheets and choose **File → Import → Upload**.
4. Import the workbook as a new spreadsheet.
5. Select **Share**.
6. Under **General access**, choose **Anyone with the link** and set access to **Viewer**.
7. Copy the normal Google Sheets share link.
8. Return to Career Accelerator and select **Paste Google Sheet Link**.

Career Accelerator verifies the link immediately by requesting an Excel export. A restricted sheet, sign-in page, non-Google URL, or invalid workbook is rejected with a specific explanation.

## Every lesson after setup

1. Select **Open Google Sheet**.
2. Open the sheet named in the lesson.
3. Complete the numbered Google Sheets task exactly as written.
4. Wait for Google Sheets to finish saving.
5. Return to Career Accelerator and select **Check My Work**.

Career Accelerator downloads the latest `.xlsx` export into the managed local workbook cache and then runs the lesson’s existing workbook validator.

## Replacing or restarting the workbook

- Select **Replace Google Sheet Link** to link a different workbook.
- Select **Get Starter Workbook** to save another clean copy of the template.
- Import the clean copy into Google Sheets and replace the saved link when you intentionally want to restart the spreadsheet pathway.

## Privacy and access

Spreadsheet Academy stores only:

- the spreadsheet ID
- the canonical share link
- the most recent synchronization time

It does not store a Google password, OAuth client, access token, refresh token, or client JSON file.

Because validation is unauthenticated, the workbook must be readable through **Anyone with the link → Viewer**. Use only the synthetic Northstar Operations practice data in this workbook. Do not add private, employer, customer, health, financial, or other sensitive information.

## Troubleshooting

**Career Accelerator says Google returned a sign-in page**  
Confirm that General access is **Anyone with the link**, not **Restricted**.

**The link is rejected**  
Copy the link from the Google Sheets **Share** dialog. Do not paste a browser search result, Drive folder link, or published HTML page.

**Check My Work sees an older result**  
Wait for the “Saved to Drive” status in Google Sheets, then check again.

**A work or school account does not allow public links**  
Create the practice workbook with a personal Google account whose sharing policy permits **Anyone with the link**.
