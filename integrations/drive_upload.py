from __future__ import annotations

import json
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path


DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


@dataclass(frozen=True)
class DriveUploadResult:
    local_path: Path
    drive_file_id: str
    drive_file_name: str
    web_view_link: str | None


def upload_folder_to_drive(
    local_folder: Path,
    drive_folder_id: str,
    service_account_path: Path | None = None,
    oauth_client_secret_path: Path | None = None,
    oauth_token_path: Path | None = None,
    file_glob: str = "*.csv",
    show_progress: bool = True,
) -> list[DriveUploadResult]:
    oauth_client_secret_path = oauth_client_secret_path or env_path("GOOGLE_OAUTH_CLIENT_SECRET")
    oauth_token_path = oauth_token_path or env_path("GOOGLE_OAUTH_TOKEN", "token.json")
    service_account_path = service_account_path or env_path("GOOGLE_APPLICATION_CREDENTIALS")

    files = sorted(local_folder.glob(file_glob))
    if not files:
        raise FileNotFoundError(f"No files matching {file_glob!r} found in {local_folder}")

    service, identity_hint = build_drive_service(
        service_account_path=service_account_path,
        oauth_client_secret_path=oauth_client_secret_path,
        oauth_token_path=oauth_token_path,
    )
    verify_drive_folder_access(service, drive_folder_id, identity_hint)
    results: list[DriveUploadResult] = []
    total = len(files)
    for index, path in enumerate(files, start=1):
        if show_progress:
            percent = int((index - 1) / total * 100)
            print(f"[{index}/{total}] {percent}% uploading {path.name}...")
        result = upload_file(service, path, drive_folder_id)
        results.append(result)
        if show_progress:
            percent = int(index / total * 100)
            print(f"[{index}/{total}] {percent}% uploaded {path.name}")
    return results


def env_path(key: str, default: str = "") -> Path | None:
    value = os.environ.get(key, default)
    if not value:
        return None
    return Path(value).expanduser()


def build_drive_service(
    service_account_path: Path | None = None,
    oauth_client_secret_path: Path | None = None,
    oauth_token_path: Path | None = None,
):
    if oauth_client_secret_path and oauth_client_secret_path.exists():
        return build_drive_service_with_oauth(oauth_client_secret_path, oauth_token_path or Path("token.json"))
    if service_account_path and service_account_path.exists():
        return build_drive_service_with_service_account(service_account_path)
    if oauth_client_secret_path:
        raise FileNotFoundError(f"GOOGLE_OAUTH_CLIENT_SECRET path does not exist: {oauth_client_secret_path}")
    if service_account_path:
        raise FileNotFoundError(f"GOOGLE_APPLICATION_CREDENTIALS path does not exist: {service_account_path}")
    raise FileNotFoundError(
        "Google Drive auth not configured. For My Drive uploads, set GOOGLE_OAUTH_CLIENT_SECRET "
        "to an OAuth client JSON path. For Shared Drive/service-account uploads, set "
        "GOOGLE_APPLICATION_CREDENTIALS to a service-account JSON path."
    )


def build_drive_service_with_service_account(service_account_path: Path):
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise ImportError(
            "Google Drive upload requires google-api-python-client and google-auth. "
            "Install them with: .venv/bin/pip install -r requirements.txt"
        ) from exc

    credentials = service_account.Credentials.from_service_account_file(
        service_account_path,
        scopes=DRIVE_SCOPES,
    )
    return build("drive", "v3", credentials=credentials), read_service_account_email(service_account_path)


def build_drive_service_with_oauth(client_secret_path: Path, token_path: Path):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise ImportError(
            "OAuth Drive upload requires google-api-python-client, google-auth, and "
            "google-auth-oauthlib. Install them with: .venv/bin/pip install -r requirements.txt"
        ) from exc

    credentials = None
    token_path = token_path.expanduser()
    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(token_path, DRIVE_SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, DRIVE_SCOPES)
            credentials = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
    return build("drive", "v3", credentials=credentials), "OAuth user"


def upload_file(service, local_path: Path, drive_folder_id: str) -> DriveUploadResult:
    try:
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise ImportError(
            "Google Drive upload requires google-api-python-client. "
            "Install it with: .venv/bin/pip install -r requirements.txt"
        ) from exc

    mime_type = mimetypes.guess_type(local_path.name)[0] or "text/csv"
    media = MediaFileUpload(local_path, mimetype=mime_type, resumable=False)
    metadata = {
        "name": local_path.name,
        "parents": [drive_folder_id],
    }
    created = (
        service.files()
        .create(
            body=metadata,
            media_body=media,
            fields="id,name,webViewLink",
            supportsAllDrives=True,
        )
        .execute()
    )
    return DriveUploadResult(
        local_path=local_path,
        drive_file_id=created["id"],
        drive_file_name=created["name"],
        web_view_link=created.get("webViewLink"),
    )


def verify_drive_folder_access(service, drive_folder_id: str, identity_hint: str) -> None:
    try:
        folder = (
            service.files()
            .get(
                fileId=drive_folder_id,
                fields="id,name,mimeType",
                supportsAllDrives=True,
            )
            .execute()
        )
    except Exception as exc:
        raise PermissionError(
            "Google Drive folder is not accessible to the configured Drive identity. "
            f"Identity: {identity_hint}. "
            f"Folder ID used: {drive_folder_id}"
        ) from exc

    if folder.get("mimeType") != "application/vnd.google-apps.folder":
        raise ValueError(f"Drive ID is accessible but is not a folder: {drive_folder_id}")


def read_service_account_email(service_account_path: Path) -> str:
    try:
        data = json.loads(service_account_path.read_text(encoding="utf-8"))
        return data.get("client_email", "<client_email missing from JSON>")
    except Exception:
        return "<could not read client_email from service account JSON>"
