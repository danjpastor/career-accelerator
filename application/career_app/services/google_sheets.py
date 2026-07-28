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


def create_applied_lab_spreadsheet(
    *,
    title: str,
    source_tables: dict[str, tuple[Iterable[str], Iterable[Iterable[Any]]]],
) -> dict[str, Any]:
    """Create the guided Google Sheets artifact for Applied Lab 01.

    Raw source tabs are populated and protected with warning-only protection.
    Analysis tabs contain structure and guidance, but no completed learner formulas.
    """
    sheets, drive = _services()
    core_tabs = [
        "START HERE",
        "Controls",
        "Order Analysis",
        "Management Summary",
        "Reconciliation",
        "Data Dictionary",
    ]
    raw_tabs = [f"{name[:80]} - Raw" for name in source_tables]
    requested_tabs = core_tabs + raw_tabs
    spreadsheet = sheets.spreadsheets().create(
        body={
            "properties": {"title": title},
            "sheets": [{"properties": {"title": name}} for name in requested_tabs],
        },
        fields="spreadsheetId,spreadsheetUrl,sheets.properties",
    ).execute()
    spreadsheet_id = str(spreadsheet["spreadsheetId"])
    properties = spreadsheet.get("sheets") or []
    ids = {
        str(row.get("properties", {}).get("title")): int(row.get("properties", {}).get("sheetId", 0))
        for row in properties
    }

    starter_values = {
        "START HERE": [
            ["Northstar Operations — Google Sheets Analyst Lab"],
            ["Purpose", "Build a controlled one-row-per-order analysis and management summary."],
            ["Workflow", "Review raw tabs → define grain → build Order Analysis → add Controls → build pivots/charts → reconcile revenue → complete handoff."],
            ["Rule", "Do not edit the Raw tabs. Build calculations in the analysis tabs."],
            ["Required output", "Management Summary with five KPIs, a regional comparison, two decision-supporting charts, and documented limitations."],
        ],
        "Controls": [
            ["Control", "Selected value", "Definition / allowed values"],
            ["Month", "All", "All or a valid reporting month from the source data"],
            ["Region", "All", "All or a valid customer region"],
            ["KPI definitions", "", "Document numerator, denominator, date rule, and missing-data behavior"],
            ["Assumptions", "", "Record exclusions, data-quality decisions, and refresh steps"],
        ],
        "Order Analysis": [[
            "order_id", "order_date", "customer_id", "customer_name", "region",
            "product_id", "product_name", "quantity", "unit_price", "returned_quantity",
            "gross_revenue", "net_revenue", "quality_flag"
        ]],
        "Management Summary": [
            ["Management Summary"],
            ["Selected month", "=Controls!B2", "Selected region", "=Controls!B3"],
            ["KPI", "Value", "Definition"],
            ["Order count", "", "Unique orders after filters"],
            ["Gross revenue", "", "Quantity × unit price before returns"],
            ["Net revenue", "", "Revenue after returned quantity"],
            ["Return rate", "", "Document the chosen denominator"],
            ["On-time ticket rate", "", "Document treatment of open tickets"],
        ],
        "Reconciliation": [["Month", "Calculated net revenue", "Finance report revenue", "Difference", "Status", "Explanation"]],
        "Data Dictionary": [["Sheet", "Field", "Meaning", "Data type", "Source / formula", "Notes"]],
    }
    for tab, values in starter_values.items():
        sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{tab}'!A1",
            valueInputOption="USER_ENTERED",
            body={"values": values},
        ).execute()

    for (table_name, (headers, rows)), tab in zip(source_tables.items(), raw_tabs):
        values = [list(headers)] + [list(row) for row in rows]
        for start in range(0, len(values), 500):
            sheets.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"'{tab}'!A{start + 1}",
                valueInputOption="RAW",
                body={"values": values[start:start + 500]},
            ).execute()

    requests: list[dict[str, Any]] = []
    for tab in requested_tabs:
        sheet_id = ids.get(tab)
        if sheet_id is None:
            continue
        requests.extend([
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                    "fields": "gridProperties.frozenRowCount",
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                    "fields": "userEnteredFormat.textFormat.bold",
                }
            },
        ])
    for tab in raw_tabs:
        sheet_id = ids.get(tab)
        if sheet_id is not None:
            requests.append({
                "protectRange": {
                    "protectedRange": {
                        "range": {"sheetId": sheet_id},
                        "description": "Raw source tab managed by Career Accelerator",
                        "warningOnly": True,
                    }
                }
            })
    if requests:
        sheets.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests},
        ).execute()
    drive.files().get(fileId=spreadsheet_id, fields="id,name,modifiedTime").execute()
    return {
        "spreadsheet_id": spreadsheet_id,
        "spreadsheet_url": spreadsheet.get(
            "spreadsheetUrl",
            f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
        ),
        "source_tabs": raw_tabs,
        "analysis_tabs": core_tabs,
    }
