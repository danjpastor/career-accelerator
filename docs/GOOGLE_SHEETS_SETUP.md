# Google Sheets connection setup

Career Accelerator uses a Google OAuth **Desktop app** client so the local application can create and read only the practice workbook you authorize.

## One-time Google Cloud setup

1. Open Google Cloud Console and create or select a project.
2. Enable **Google Drive API**.
3. Configure the OAuth consent screen. For personal testing, add your own Google account as a test user.
4. Create credentials: **OAuth client ID → Desktop app**.
5. Download the client JSON file.
6. In Spreadsheet Academy, click **Connect Google Sheets** and select that JSON file.
7. Approve access in your browser. Career Accelerator stores the OAuth token locally under `data/google_sheets/`.

## Normal lesson workflow

1. Click **Open Google Sheet**.
2. Complete the exact Google Sheets steps shown in the lesson.
3. Return to Career Accelerator and click **Check My Work**.

Career Accelerator exports the linked native Google Sheet to a temporary `.xlsx` synchronization copy and runs the existing v10.29 workbook validator. You do not manually download or upload a workbook for each lesson.

## Disconnecting

Delete these local files while Career Accelerator is closed:

- `data/google_sheets/google_oauth_token.json`
- `data/google_sheets/spreadsheet_academy.json`

This does not delete the Google Sheet from Google Drive.
