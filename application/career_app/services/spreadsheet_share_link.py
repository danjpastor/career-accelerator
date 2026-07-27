from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


STATE_DIRECTORY = Path("data/google_sheets")
STATE_FILENAME = "spreadsheet_academy.json"
EXPORT_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class SpreadsheetShareLinkError(RuntimeError):
    """Raised when a shared Google Sheet cannot be used for validation."""


def _safe_json_load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def extract_spreadsheet_id(value: str) -> str | None:
    """Extract a Google spreadsheet ID from a normal share link or raw ID."""

    text = str(value or "").strip()
    if not text:
        return None

    match = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", text)
    if match:
        return match.group(1)

    match = re.search(r"[?&]id=([A-Za-z0-9_-]+)", text)
    if match:
        return match.group(1)

    if re.fullmatch(r"[A-Za-z0-9_-]{20,}", text):
        return text
    return None


def canonical_share_url(spreadsheet_id: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


def export_url(spreadsheet_id: str) -> str:
    return (
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?"
        + urllib.parse.urlencode({"format": "xlsx", "exportFormat": "xlsx"})
    )


class SpreadsheetShareLink:
    """Persist and download one public Google Sheet for Spreadsheet Academy.

    The learner grants access with Google Sheets' ordinary "Anyone with the
    link" viewer setting. Career Accelerator stores only the share URL and
    spreadsheet ID. No OAuth client, access token, refresh token, or Google
    account credentials are required.
    """

    def __init__(self, repository_root: str | Path):
        self.root = Path(repository_root).resolve()
        self.state_dir = self.root / STATE_DIRECTORY
        self.state_path = self.state_dir / STATE_FILENAME
        self.state = _safe_json_load(self.state_path)
        self._migrate_legacy_state()

    def _migrate_legacy_state(self) -> None:
        original = dict(self.state)
        spreadsheet_id = extract_spreadsheet_id(
            str(
                self.state.get("share_url")
                or self.state.get("spreadsheet_url")
                or self.state.get("spreadsheet_id")
                or ""
            )
        )
        if spreadsheet_id:
            self.state["schema_version"] = 2
            self.state["mode"] = "public_share_link"
            self.state["spreadsheet_id"] = spreadsheet_id
            self.state["share_url"] = canonical_share_url(spreadsheet_id)
        for key in (
            "oauth_client_id",
            "client_id",
            "access_token",
            "refresh_token",
            "token",
        ):
            self.state.pop(key, None)
        if self.state != original:
            if self.state:
                _atomic_json_write(self.state_path, self.state)
            else:
                self.state_path.unlink(missing_ok=True)

    @property
    def spreadsheet_id(self) -> str | None:
        return extract_spreadsheet_id(str(self.state.get("spreadsheet_id") or ""))

    @property
    def share_url(self) -> str | None:
        spreadsheet_id = self.spreadsheet_id
        if not spreadsheet_id:
            return None
        return canonical_share_url(spreadsheet_id)

    @property
    def linked(self) -> bool:
        return self.spreadsheet_id is not None

    def save_link(self, value: str, *, verify: bool = True) -> str:
        spreadsheet_id = extract_spreadsheet_id(value)
        if not spreadsheet_id:
            raise SpreadsheetShareLinkError(
                "That is not a valid Google Sheets share link. Copy the link "
                "from Share → Copy link in Google Sheets."
            )
        if verify:
            self.download_bytes(spreadsheet_id=spreadsheet_id)
        self.state = {
            "schema_version": 2,
            "mode": "public_share_link",
            "spreadsheet_id": spreadsheet_id,
            "share_url": canonical_share_url(spreadsheet_id),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        _atomic_json_write(self.state_path, self.state)
        return self.state["share_url"]

    def clear(self) -> None:
        self.state = {}
        try:
            self.state_path.unlink()
        except FileNotFoundError:
            pass

    def download_bytes(self, *, spreadsheet_id: str | None = None) -> bytes:
        spreadsheet_id = spreadsheet_id or self.spreadsheet_id
        if not spreadsheet_id:
            raise SpreadsheetShareLinkError(
                "Paste your Google Sheets share link before checking this lesson."
            )

        request = urllib.request.Request(
            export_url(spreadsheet_id),
            method="GET",
            headers={
                "User-Agent": "Career-Accelerator-Spreadsheet-Academy/10.31",
                "Accept": EXPORT_MIME + ",application/octet-stream;q=0.9,*/*;q=0.1",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                content_type = str(response.headers.get("Content-Type") or "").casefold()
                data = response.read(55 * 1024 * 1024)
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403, 404}:
                raise SpreadsheetShareLinkError(
                    "Career Accelerator cannot read that Google Sheet. In Google "
                    "Sheets, choose Share and set General access to “Anyone with "
                    "the link” with Viewer access, then paste the link again."
                ) from exc
            raise SpreadsheetShareLinkError(
                f"Google returned HTTP {exc.code} while downloading the workbook."
            ) from exc
        except urllib.error.URLError as exc:
            raise SpreadsheetShareLinkError(
                f"Could not reach Google Sheets: {getattr(exc, 'reason', exc)}"
            ) from exc

        if len(data) >= 55 * 1024 * 1024:
            raise SpreadsheetShareLinkError(
                "The shared workbook is too large to validate safely."
            )
        if not data.startswith(b"PK"):
            if "text/html" in content_type or data.lstrip().startswith((b"<!DOCTYPE", b"<html")):
                raise SpreadsheetShareLinkError(
                    "Google returned a sign-in or access page instead of the workbook. "
                    "Set General access to “Anyone with the link” with Viewer access."
                )
            raise SpreadsheetShareLinkError(
                "Google did not return a valid Excel workbook export for that link."
            )
        return data

    def sync_to(self, destination: str | Path) -> Path:
        data = self.download_bytes()
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".google-download.tmp")
        try:
            temporary.write_bytes(data)
            temporary.replace(target)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        self.state["last_sync_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            self.state["last_sync_target"] = str(target.relative_to(self.root))
        except ValueError:
            self.state["last_sync_target"] = str(target)
        _atomic_json_write(self.state_path, self.state)
        return target
