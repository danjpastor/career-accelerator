from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import secrets
import shutil
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Iterable

from PySide6.QtCore import QEvent, QObject, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QLabel,
    QLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

GOOGLE_DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
GOOGLE_EXPORT_MIME = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
GOOGLE_SHEET_MIME = "application/vnd.google-apps.spreadsheet"
STATE_FOLDER = Path("data/google_sheets")
STATE_FILENAME = "spreadsheet_academy.json"
TOKEN_FILENAME = "google_oauth_token.json"
CLIENT_FILENAME = "google_oauth_client.json"
SYNC_FILENAME = "Northstar Operations Practice Workbook.xlsx"


class GoogleSheetsError(RuntimeError):
    pass


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _safe_json_load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _extract_spreadsheet_id(value: str) -> str | None:
    value = str(value or "").strip()
    if not value:
        return None
    match = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", value)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{20,}", value):
        return value
    return None


def _iter_object_paths(value: Any, *, depth: int = 0) -> Iterable[Path]:
    if depth > 2 or value is None:
        return
    if isinstance(value, Path):
        yield value
        return
    if isinstance(value, str):
        if value.lower().endswith(".xlsx"):
            yield Path(value)
        return
    if isinstance(value, dict):
        for child in value.values():
            yield from _iter_object_paths(child, depth=depth + 1)
        return
    if isinstance(value, (tuple, list, set)):
        for child in value:
            yield from _iter_object_paths(child, depth=depth + 1)


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    result: dict[str, str] = {}
    completed = threading.Event()
    expected_state = ""

    def do_GET(self) -> None:  # noqa: N802 - inherited API name
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        returned_state = query.get("state", [""])[0]
        if returned_state != self.__class__.expected_state:
            self.__class__.result = {"error": "Google returned an invalid authorization state."}
            message = "Google authorization could not be verified."
            status = 400
        elif "code" in query:
            self.__class__.result = {"code": query["code"][0]}
            message = (
                "Google Sheets is connected. You can close this browser tab "
                "and return to Career Accelerator."
            )
            status = 200
        else:
            self.__class__.result = {
                "error": query.get("error", ["Authorization was cancelled."])[0]
            }
            message = "Google authorization was not completed."
            status = 400
        body = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<title>Career Accelerator</title></head>"
            "<body style='font-family:Segoe UI,Arial;padding:32px'>"
            f"<h2>{message}</h2></body></html>"
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.__class__.completed.set()

    def log_message(self, _format: str, *_args: Any) -> None:
        return


class GoogleSheetsWorkbookManager(QObject):
    """Manage one continuing Google Sheet and synchronize it for validation."""

    def __init__(self, window: QWidget, repository_root: Path):
        super().__init__(window)
        self.window = window
        self.root = Path(repository_root).resolve()
        self.data_dir = self.root / STATE_FOLDER
        self.state_path = self.data_dir / STATE_FILENAME
        self.token_path = self.data_dir / TOKEN_FILENAME
        self.client_path = self.data_dir / CLIENT_FILENAME
        self.sync_path = self.data_dir / SYNC_FILENAME
        self.state = _safe_json_load(self.state_path, {})
        if not isinstance(self.state, dict):
            self.state = {}
        self._scan_timer = QTimer(self)
        self._scan_timer.setInterval(700)
        self._scan_timer.timeout.connect(self.patch_workbook_controls)
        self._scan_timer.start()
        QTimer.singleShot(0, self.patch_workbook_controls)

    @property
    def spreadsheet_id(self) -> str | None:
        return _extract_spreadsheet_id(str(self.state.get("spreadsheet_id", "")))

    @property
    def spreadsheet_url(self) -> str | None:
        spreadsheet_id = self.spreadsheet_id
        if not spreadsheet_id:
            return None
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

    def _save_state(self) -> None:
        self.state["schema_version"] = 1
        self.state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        _atomic_json_write(self.state_path, self.state)

    def _select_client_file(self) -> Path:
        guide = self.root / "docs" / "GOOGLE_SHEETS_SETUP.md"
        detail = (
            "Career Accelerator needs a Google OAuth Desktop client JSON file "
            "once. This file identifies your local app to Google; it does not "
            "contain your Google password."
        )
        if guide.is_file():
            detail += f"\n\nSetup guide:\n{guide}"
        QMessageBox.information(
            self.window,
            "Connect Google Sheets",
            detail,
        )
        selected, _ = QFileDialog.getOpenFileName(
            self.window,
            "Select Google OAuth Desktop Client JSON",
            str(Path.home()),
            "JSON files (*.json)",
        )
        if not selected:
            raise GoogleSheetsError("Google connection was cancelled.")
        source = Path(selected)
        payload = _safe_json_load(source, {})
        installed = payload.get("installed") if isinstance(payload, dict) else None
        if not isinstance(installed, dict) or not installed.get("client_id"):
            raise GoogleSheetsError(
                "That file is not a Google OAuth Desktop client JSON file."
            )
        self.data_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, self.client_path)
        return self.client_path

    def _client_config(self) -> dict[str, Any]:
        path = self.client_path if self.client_path.is_file() else self._select_client_file()
        payload = _safe_json_load(path, {})
        installed = payload.get("installed") if isinstance(payload, dict) else None
        if not isinstance(installed, dict):
            raise GoogleSheetsError("The saved Google OAuth client file is invalid.")
        return installed

    def _request(
        self,
        url: str,
        *,
        method: str = "GET",
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 90,
    ) -> bytes:
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers=headers or {},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(detail)
                detail = payload.get("error", {}).get("message", detail)
            except (ValueError, AttributeError):
                pass
            raise GoogleSheetsError(
                f"Google returned HTTP {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise GoogleSheetsError(
                f"Could not reach Google: {getattr(exc, 'reason', exc)}"
            ) from exc

    def _refresh_token(self, token: dict[str, Any]) -> dict[str, Any]:
        client = self._client_config()
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            raise GoogleSheetsError("Google authorization must be renewed.")
        payload = urllib.parse.urlencode(
            {
                "client_id": client["client_id"],
                "client_secret": client.get("client_secret", ""),
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode("utf-8")
        response = json.loads(
            self._request(
                str(client.get("token_uri") or "https://oauth2.googleapis.com/token"),
                method="POST",
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ).decode("utf-8")
        )
        token.update(response)
        token["expires_at"] = time.time() + int(response.get("expires_in", 3600))
        _atomic_json_write(self.token_path, token)
        return token

    def _authorize(self) -> dict[str, Any]:
        client = self._client_config()
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        state = secrets.token_urlsafe(24)

        _OAuthCallbackHandler.result = {}
        _OAuthCallbackHandler.completed = threading.Event()
        _OAuthCallbackHandler.expected_state = state
        server = HTTPServer(("127.0.0.1", 0), _OAuthCallbackHandler)
        server.timeout = 1
        port = int(server.server_address[1])
        redirect_uri = f"http://127.0.0.1:{port}/"

        def serve() -> None:
            try:
                while not _OAuthCallbackHandler.completed.is_set():
                    server.handle_request()
            finally:
                server.server_close()

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()

        params = {
            "client_id": client["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": GOOGLE_DRIVE_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        }
        authorization_url = (
            str(client.get("auth_uri") or "https://accounts.google.com/o/oauth2/auth")
            + "?"
            + urllib.parse.urlencode(params)
        )
        webbrowser.open(authorization_url)
        if not _OAuthCallbackHandler.completed.wait(300):
            server.server_close()
            raise GoogleSheetsError("Google authorization did not finish.")
        result = dict(_OAuthCallbackHandler.result)
        if result.get("error"):
            raise GoogleSheetsError(result["error"])
        code = result.get("code")
        if not code:
            raise GoogleSheetsError("Google did not return an authorization code.")

        payload = urllib.parse.urlencode(
            {
                "client_id": client["client_id"],
                "client_secret": client.get("client_secret", ""),
                "code": code,
                "code_verifier": verifier,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }
        ).encode("utf-8")
        token = json.loads(
            self._request(
                str(client.get("token_uri") or "https://oauth2.googleapis.com/token"),
                method="POST",
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ).decode("utf-8")
        )
        token["expires_at"] = time.time() + int(token.get("expires_in", 3600))
        _atomic_json_write(self.token_path, token)
        return token

    def _access_token(self) -> str:
        token = _safe_json_load(self.token_path, {})
        if not isinstance(token, dict) or not token.get("access_token"):
            token = self._authorize()
        elif float(token.get("expires_at", 0)) <= time.time() + 90:
            try:
                token = self._refresh_token(token)
            except GoogleSheetsError:
                try:
                    self.token_path.unlink()
                except OSError:
                    pass
                token = self._authorize()
        access_token = str(token.get("access_token", ""))
        if not access_token:
            raise GoogleSheetsError("Google did not provide an access token.")
        return access_token

    def _authorized_request(
        self,
        url: str,
        *,
        method: str = "GET",
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        all_headers = dict(headers or {})
        all_headers["Authorization"] = f"Bearer {self._access_token()}"
        return self._request(url, method=method, data=data, headers=all_headers)

    def _candidate_xlsx_files(self) -> list[Path]:
        excluded_parts = {
            ".git",
            ".venv",
            "patch_backups",
            "backups",
            "archive",
            "__pycache__",
        }
        candidates: list[Path] = []
        for path in self.root.rglob("*.xlsx"):
            relative_parts = {part.casefold() for part in path.relative_to(self.root).parts}
            if relative_parts & excluded_parts:
                continue
            candidates.append(path)
        return candidates

    def _template_path(self) -> Path:
        candidates = self._candidate_xlsx_files()
        ranked: list[tuple[int, Path]] = []
        for path in candidates:
            name = path.name.casefold()
            full = str(path).casefold()
            score = 0
            if "northstar" in name:
                score += 12
            if "practice workbook" in name:
                score += 9
            if "template" in name or "starter" in name:
                score += 7
            if "curriculum" in full or "assets" in full:
                score += 4
            if path.resolve() == self.sync_path.resolve():
                score -= 30
            ranked.append((score, path))
        ranked.sort(key=lambda item: (-item[0], len(str(item[1]))))
        if not ranked or ranked[0][0] <= 0:
            raise GoogleSheetsError(
                "The Northstar Operations workbook template could not be found."
            )
        return ranked[0][1]

    def _upload_template(self, template: Path, title: str) -> dict[str, Any]:
        metadata = {"name": title, "mimeType": GOOGLE_SHEET_MIME}
        boundary = "dca_" + secrets.token_hex(16)
        body = (
            f"--{boundary}\r\n"
            "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        ).encode("utf-8")
        body += _json_bytes(metadata)
        body += (
            f"\r\n--{boundary}\r\n"
            f"Content-Type: {GOOGLE_EXPORT_MIME}\r\n\r\n"
        ).encode("utf-8")
        body += template.read_bytes()
        body += f"\r\n--{boundary}--\r\n".encode("utf-8")
        response = self._authorized_request(
            "https://www.googleapis.com/upload/drive/v3/files"
            "?uploadType=multipart&fields=id,name,mimeType,webViewLink",
            method="POST",
            data=body,
            headers={"Content-Type": f"multipart/related; boundary={boundary}"},
        )
        payload = json.loads(response.decode("utf-8"))
        if not payload.get("id"):
            raise GoogleSheetsError("Google did not return a spreadsheet ID.")
        return payload

    def create_new_workbook(self, *, confirm_replace: bool = True) -> None:
        if self.spreadsheet_id and confirm_replace:
            answer = QMessageBox.question(
                self.window,
                "Start a Fresh Practice Workbook?",
                (
                    "This creates a new Northstar Operations Google Sheet and "
                    "links Career Accelerator to it. Your current Google Sheet "
                    "will remain in Drive and will not be deleted."
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        template = self._template_path()
        title = "Northstar Operations Practice Workbook"
        payload = self._upload_template(template, title)
        self.state.update(
            {
                "spreadsheet_id": payload["id"],
                "spreadsheet_name": payload.get("name", title),
                "spreadsheet_url": payload.get("webViewLink")
                or f"https://docs.google.com/spreadsheets/d/{payload['id']}/edit",
                "source_template": str(template.relative_to(self.root)),
            }
        )
        self._save_state()
        self.open_workbook()
        QMessageBox.information(
            self.window,
            "Practice Workbook Ready",
            (
                "Your continuing Northstar Operations workbook is linked. "
                "Use this same Google Sheet for every Spreadsheet Academy lesson."
            ),
        )
        self.patch_workbook_controls()

    def link_existing_workbook(self) -> None:
        value, accepted = QInputDialog.getText(
            self.window,
            "Link Existing Google Sheet",
            "Paste the Google Sheets link:",
        )
        if not accepted:
            return
        spreadsheet_id = _extract_spreadsheet_id(value)
        if not spreadsheet_id:
            raise GoogleSheetsError("That is not a valid Google Sheets link.")
        # Confirm access immediately. drive.file access works for files created by
        # this app and files explicitly authorized for this OAuth client.
        self._authorized_request(
            "https://www.googleapis.com/drive/v3/files/"
            f"{urllib.parse.quote(spreadsheet_id)}?fields=id,name,mimeType,webViewLink"
        )
        self.state.update(
            {
                "spreadsheet_id": spreadsheet_id,
                "spreadsheet_url": (
                    f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
                ),
            }
        )
        self._save_state()
        self.open_workbook()
        self.patch_workbook_controls()

    def connect_or_create(self) -> None:
        try:
            self._access_token()
            if self.spreadsheet_id:
                answer = QMessageBox.question(
                    self.window,
                    "Google Sheets Connected",
                    (
                        "A practice workbook is already linked. Choose Yes to "
                        "open it. Choose No to replace the link or create a fresh workbook."
                    ),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if answer == QMessageBox.StandardButton.Yes:
                    self.open_workbook()
                    return
            choice, accepted = QInputDialog.getItem(
                self.window,
                "Set Up Practice Workbook",
                "How should Career Accelerator set up your workbook?",
                [
                    "Create my Northstar Operations workbook",
                    "Link an existing Google Sheet",
                ],
                0,
                False,
            )
            if not accepted:
                return
            if str(choice).startswith("Create"):
                self.create_new_workbook(confirm_replace=False)
            else:
                self.link_existing_workbook()
        except GoogleSheetsError as exc:
            QMessageBox.warning(self.window, "Google Sheets", str(exc))

    def open_workbook(self) -> None:
        url = self.spreadsheet_url
        if not url:
            self.connect_or_create()
            return
        if not QDesktopServices.openUrl(QUrl(url)):
            webbrowser.open(url)

    def _discover_validator_targets(self) -> list[Path]:
        found: list[Path] = [self.sync_path]
        try:
            template_resolved = self._template_path().resolve()
        except (GoogleSheetsError, OSError):
            template_resolved = None
        academy_objects: list[Any] = []
        for widget in self.window.findChildren(QWidget):
            class_name = widget.__class__.__name__.casefold()
            if "academy" in class_name:
                academy_objects.append(widget)
                service = getattr(widget, "service", None)
                if service is not None:
                    academy_objects.append(service)
        for obj in academy_objects:
            try:
                attributes = vars(obj)
            except TypeError:
                continue
            for name, value in attributes.items():
                lowered = str(name).casefold()
                if any(token in lowered for token in ("template", "starter", "source")):
                    continue
                if not any(token in lowered for token in ("workbook", "xlsx", "submission", "path")):
                    continue
                for path in _iter_object_paths(value):
                    if path.suffix.casefold() != ".xlsx":
                        continue
                    absolute = path if path.is_absolute() else self.root / path
                    try:
                        if template_resolved is not None and absolute.resolve() == template_resolved:
                            continue
                    except OSError:
                        pass
                    found.append(absolute)
        for module_name, module in tuple(sys.modules.items()):
            if not module_name.startswith("career_app") or not any(
                token in module_name.casefold() for token in ("workbook", "spreadsheet", "academy")
            ):
                continue
            try:
                module_values = vars(module)
            except TypeError:
                continue
            for name, value in module_values.items():
                lowered = str(name).casefold()
                if any(token in lowered for token in ("template", "starter", "source")):
                    continue
                if not any(token in lowered for token in ("workbook", "xlsx", "submission", "path")):
                    continue
                for path in _iter_object_paths(value):
                    if path.suffix.casefold() != ".xlsx":
                        continue
                    absolute = path if path.is_absolute() else self.root / path
                    try:
                        if template_resolved is not None and absolute.resolve() == template_resolved:
                            continue
                    except OSError:
                        pass
                    found.append(absolute)
        for path in self._candidate_xlsx_files():
            name = path.name.casefold()
            full = str(path).casefold()
            if any(token in name for token in ("template", "starter", "capstone", "snapshot")):
                continue
            if any(token in full for token in ("curriculum", "assets", "evidence", "archive", "backup")):
                continue
            try:
                if template_resolved is not None and path.resolve() == template_resolved:
                    continue
            except OSError:
                pass
            if "northstar" in name or "practice workbook" in name:
                if any(token in full for token in ("workspaces", "submission", "practice", "learner")):
                    found.append(path)
        unique: list[Path] = []
        seen: set[str] = set()
        for path in found:
            try:
                normalized = str(path.resolve()).casefold()
            except OSError:
                normalized = str(path.absolute()).casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            unique.append(path)
        return unique

    def export_for_validation(self) -> list[Path]:
        spreadsheet_id = self.spreadsheet_id
        if not spreadsheet_id:
            raise GoogleSheetsError(
                "Connect the Spreadsheet Academy to Google Sheets before checking your work."
            )
        data = self._authorized_request(
            "https://www.googleapis.com/drive/v3/files/"
            f"{urllib.parse.quote(spreadsheet_id)}/export?"
            + urllib.parse.urlencode({"mimeType": GOOGLE_EXPORT_MIME})
        )
        if len(data) < 1000 or not data.startswith(b"PK"):
            raise GoogleSheetsError("Google did not return a valid workbook export.")
        written: list[Path] = []
        for path in self._discover_validator_targets():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(path.suffix + ".google-sync.tmp")
                temporary.write_bytes(data)
                temporary.replace(path)
                written.append(path)
            except OSError:
                continue
        if not written:
            raise GoogleSheetsError(
                "The Google Sheet was downloaded, but the local validator workbook could not be updated."
            )
        self.state["last_sync_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.state["last_sync_targets"] = [
            str(path.relative_to(self.root)) if path.is_relative_to(self.root) else str(path)
            for path in written
        ]
        self._save_state()
        return written

    def sync_before_check(self) -> None:
        button = self.sender()
        try:
            self.export_for_validation()
        except GoogleSheetsError as exc:
            if isinstance(button, QPushButton):
                button.blockSignals(True)
                QTimer.singleShot(0, lambda b=button: b.blockSignals(False))
            QMessageBox.warning(self.window, "Could Not Check Google Sheet", str(exc))

    @staticmethod
    def _disconnect_clicked(button: QPushButton) -> None:
        try:
            button.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass

    def patch_workbook_controls(self) -> None:
        linked = bool(self.spreadsheet_id)
        for button in self.window.findChildren(QPushButton):
            text = button.text().replace("&", "").strip()
            lowered = text.casefold()
            if lowered in {"use in google sheets", "connect google sheets"}:
                if not button.property("dca_google_connect"):
                    self._disconnect_clicked(button)
                    button.clicked.connect(self.connect_or_create)
                    button.setProperty("dca_google_connect", True)
                button.setText("Google Sheet Connected" if linked else "Connect Google Sheets")
                button.setToolTip(
                    "Open or replace the one Google Sheet used throughout Spreadsheet Academy."
                )
            elif lowered in {
                "open practice workbook",
                "open google sheet",
                "open linked google sheet",
            }:
                if not button.property("dca_google_open"):
                    self._disconnect_clicked(button)
                    button.clicked.connect(self.open_workbook)
                    button.setProperty("dca_google_open", True)
                button.setText("Open Google Sheet")
                button.setToolTip("Open your continuing Northstar Operations workbook.")
            elif lowered in {
                "reset lesson workbook",
                "start fresh workbook",
                "create fresh google sheet",
            }:
                if not button.property("dca_google_fresh"):
                    self._disconnect_clicked(button)
                    button.clicked.connect(
                        lambda _checked=False: self.create_new_workbook(confirm_replace=True)
                    )
                    button.setProperty("dca_google_fresh", True)
                button.setText("Start Fresh Workbook")
                button.setToolTip(
                    "Create a new clean Google Sheet. The current file remains in Drive."
                )
            elif lowered in {"open lesson instructions", "download workbook"}:
                button.hide()
            elif lowered in {"check workbook", "check my work"}:
                if not button.property("dca_google_check"):
                    button.pressed.connect(self.sync_before_check)
                    button.setProperty("dca_google_check", True)
                button.setText("Check My Work")
                button.setToolTip(
                    "Synchronize the linked Google Sheet and run the lesson validator."
                )


class ExactScrollContentFixer(QObject):
    """Keep the Next Tasks scroll range equal to the rendered row height."""

    def __init__(self, window: QWidget):
        super().__init__(window)
        self.window = window
        self.areas: list[QScrollArea] = []
        self.timer = QTimer(self)
        self.timer.setInterval(650)
        self.timer.timeout.connect(self.discover_and_sync)
        self.timer.start()
        QTimer.singleShot(0, self.discover_and_sync)

    @staticmethod
    def _is_next_tasks_label(label: QLabel) -> bool:
        text = re.sub(r"<[^>]+>", " ", label.text())
        text = re.sub(r"\s+", " ", text).strip().casefold()
        return "next tasks" in text and len(text) <= 80

    def _candidate_areas(self) -> list[QScrollArea]:
        candidates: list[QScrollArea] = []
        for label in self.window.findChildren(QLabel):
            if not self._is_next_tasks_label(label):
                continue
            parent: QWidget | None = label.parentWidget()
            for _ in range(7):
                if parent is None:
                    break
                nearby = [
                    area
                    for area in parent.findChildren(QScrollArea)
                    if area.widget() is not None
                    and not area.isAncestorOf(label)
                    and area not in candidates
                ]
                if nearby:
                    nearby.sort(key=lambda area: max(1, area.width()) * max(1, area.height()))
                    candidates.append(nearby[0])
                    break
                parent = parent.parentWidget()
        return candidates

    @staticmethod
    def _remove_trailing_expanding_spacers(layout: QLayout) -> None:
        while layout.count():
            item = layout.itemAt(layout.count() - 1)
            spacer = item.spacerItem() if item is not None else None
            if spacer is None:
                break
            vertical = spacer.expandingDirections() & Qt.Orientation.Vertical
            if not vertical and spacer.sizeHint().height() <= 1:
                break
            layout.takeAt(layout.count() - 1)

    def _register(self, area: QScrollArea) -> None:
        if area in self.areas:
            return
        self.areas.append(area)
        area.installEventFilter(self)
        area.viewport().installEventFilter(self)
        content = area.widget()
        if content is not None:
            content.installEventFilter(self)
            layout = content.layout()
            if layout is not None:
                self._remove_trailing_expanding_spacers(layout)
                layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        area.setWidgetResizable(False)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def _sync_area(self, area: QScrollArea) -> None:
        content = area.widget()
        if content is None:
            return
        layout = content.layout()
        if layout is None:
            return
        self._remove_trailing_expanding_spacers(layout)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.activate()
        viewport_width = max(0, area.viewport().width())
        height = max(0, layout.sizeHint().height())
        if layout.contentsMargins():
            margins = layout.contentsMargins()
            height = max(height, margins.top() + margins.bottom())
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        content.setMinimumSize(QSize(viewport_width, height))
        content.setMaximumHeight(height)
        content.resize(viewport_width, height)
        content.updateGeometry()
        area.verticalScrollBar().setPageStep(max(1, area.viewport().height()))
        area.verticalScrollBar().setSingleStep(max(1, min(48, height)))

    def discover_and_sync(self) -> None:
        for area in self._candidate_areas():
            self._register(area)
        for area in list(self.areas):
            try:
                self._sync_area(area)
            except RuntimeError:
                self.areas.remove(area)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in {
            QEvent.Type.LayoutRequest,
            QEvent.Type.Resize,
            QEvent.Type.Show,
            QEvent.Type.FontChange,
            QEvent.Type.StyleChange,
        }:
            QTimer.singleShot(0, self.discover_and_sync)
        return super().eventFilter(watched, event)


def install_google_sheets_academy(window: QWidget, repository_root: Path) -> None:
    """Install the v10.30.1 Google Sheets workflow and Next Tasks height repair."""
    if getattr(window, "_dca_google_sheets_academy", None) is not None:
        return
    manager = GoogleSheetsWorkbookManager(window, Path(repository_root))
    scroll_fixer = ExactScrollContentFixer(window)
    window._dca_google_sheets_academy = manager
    window._dca_next_tasks_exact_height = scroll_fixer
