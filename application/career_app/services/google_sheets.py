"""Optional Google Sheets cleaning integration.

The application remains fully usable without the optional Google libraries.
OAuth credentials and tokens are never stored in the project database.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

SCOPES = (
    "https://www.googleapis.com/auth/drive.file",
)
KEYRING_SERVICE = "Career Accelerator Google Sheets"
KEYRING_ACCOUNT = "oauth-token"
KEYRING_PROFILE_ACCOUNT = "profile-label"


class GoogleSheetsUnavailable(RuntimeError):
    pass


def _libraries():
    try:
        import keyring
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise GoogleSheetsUnavailable(
            "Google Sheets support is optional and is not installed. "
            "Open Google Sheets Setup in Files & Outputs for installation steps."
        ) from exc
    return keyring, Request, Credentials, InstalledAppFlow, build


def _load_credentials():
    keyring, Request, Credentials, _, _ = _libraries()
    raw = keyring.get_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
    if not raw:
        return None
    try:
        credentials = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)
    except Exception:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
        return None
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        keyring.set_password(
            KEYRING_SERVICE,
            KEYRING_ACCOUNT,
            credentials.to_json(),
        )
    return credentials


def connect(client_secret_path: Path) -> str:
    keyring, _, _, InstalledAppFlow, build = _libraries()
    path = Path(client_secret_path)
    if not path.is_file():
        raise FileNotFoundError("Select a Google OAuth Desktop client JSON file.")
    flow = InstalledAppFlow.from_client_secrets_file(str(path), SCOPES)
    credentials = flow.run_local_server(port=0, open_browser=True)
    keyring.set_password(KEYRING_SERVICE, KEYRING_ACCOUNT, credentials.to_json())
    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    profile = drive.about().get(fields="user(displayName,emailAddress)").execute()
    user = profile.get("user") or {}
    label = str(user.get("emailAddress") or user.get("displayName") or "Connected")
    keyring.set_password(KEYRING_SERVICE, KEYRING_PROFILE_ACCOUNT, label)
    return label


def disconnect() -> None:
    keyring, *_ = _libraries()
    for account in (KEYRING_ACCOUNT, KEYRING_PROFILE_ACCOUNT):
        try:
            keyring.delete_password(KEYRING_SERVICE, account)
        except Exception:
            pass


def connection_label() -> str:
    try:
        credentials = _load_credentials()
    except GoogleSheetsUnavailable:
        return "Optional support not installed"
    if credentials is None:
        return "Not connected"
    keyring, *_ = _libraries()
    return str(
        keyring.get_password(KEYRING_SERVICE, KEYRING_PROFILE_ACCOUNT)
        or "Connected"
    )


def _services():
    credentials = _load_credentials()
    if credentials is None:
        raise GoogleSheetsUnavailable("Connect a Google account first.")
    *_, build = _libraries()
    return (
        build("sheets", "v4", credentials=credentials, cache_discovery=False),
        build("drive", "v3", credentials=credentials, cache_discovery=False),
    )


def create_working_spreadsheet(
    *,
    title: str,
    table_name: str,
    headers: Iterable[str],
    rows: Iterable[Iterable[Any]],
) -> dict[str, str]:
    sheets, drive = _services()
    raw_title = f"{table_name}_raw_reference"[:100]
    clean_title = f"{table_name}_cleaning"[:100]
    spreadsheet = sheets.spreadsheets().create(
        body={
            "properties": {"title": title},
            "sheets": [
                {"properties": {"title": raw_title}},
                {"properties": {"title": clean_title}},
            ],
        },
        fields="spreadsheetId,spreadsheetUrl,sheets.properties",
    ).execute()
    spreadsheet_id = spreadsheet["spreadsheetId"]
    values = [list(headers)] + [list(row) for row in rows]
    chunk_size = 500
    for sheet_title in (raw_title, clean_title):
        for start in range(0, len(values), chunk_size):
            chunk = values[start : start + chunk_size]
            sheets.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"'{sheet_title}'!A{start + 1}",
                valueInputOption="RAW",
                body={"values": chunk},
            ).execute()
    raw_sheet_id = int(spreadsheet["sheets"][0]["properties"]["sheetId"])
    requests = [
        {
            "protectRange": {
                "protectedRange": {
                    "range": {"sheetId": raw_sheet_id},
                    "description": "Raw reference managed by Career Accelerator",
                    "warningOnly": True,
                }
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": raw_sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                },
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }
        },
    ]
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests},
    ).execute()
    # Touch the Drive API so drive.file ownership is established and verified.
    drive.files().get(fileId=spreadsheet_id, fields="id,name,modifiedTime").execute()
    return {
        "spreadsheet_id": spreadsheet_id,
        "spreadsheet_url": spreadsheet.get(
            "spreadsheetUrl",
            f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
        ),
        "raw_sheet": raw_title,
        "cleaning_sheet": clean_title,
    }


def read_sheet(spreadsheet_id: str, sheet_name: str) -> list[list[Any]]:
    sheets, _ = _services()
    response = sheets.spreadsheets().values().get(
        spreadsheetId=str(spreadsheet_id),
        range=f"'{sheet_name}'",
        valueRenderOption="UNFORMATTED_VALUE",
        dateTimeRenderOption="FORMATTED_STRING",
    ).execute()
    return [list(row) for row in response.get("values", [])]
