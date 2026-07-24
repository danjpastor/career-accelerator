# Optional Google Sheets Support

Google Sheets is an optional cleaning method inside **Clean and validate analytical data → Files & Outputs**. Career Accelerator opens the real Google Sheets editor in your browser. It does not clean the data for you.

## Install the optional libraries

Close Career Accelerator, open Command Prompt in the repository, and run:

```bat
.venv\Scripts\python.exe -m pip install google-api-python-client google-auth-oauthlib keyring
```

This is an explicit one-time installation. The normal application launcher and startup process do not install or check these optional packages.

## Create a Google OAuth desktop client

1. Open Google Cloud Console and create or select a project.
2. Enable the **Google Sheets API** and **Google Drive API**.
3. Configure the OAuth consent screen for your account or test users.
4. Create an OAuth client ID with application type **Desktop app**.
5. Download the client JSON file to a private location outside this repository.

## Connect inside Career Accelerator

1. Open **Clean and validate analytical data**.
2. Open **Files & Outputs**.
3. Select **Connect Google Account** and choose the OAuth desktop-client JSON.
4. Complete authorization in the browser.
5. Select a table and choose **Create Google Sheets Working Copy**.
6. Clean the data manually in the browser.
7. Return to Career Accelerator and choose **Import from Google Sheets**.

The app requests only the `drive.file` scope. The OAuth token is stored through Windows Credential Manager when `keyring` is available. Credentials are not copied into the project database or portfolio repository.
