#!/usr/bin/env python3
"""
Create a single aggregated Google Doc from local output_*.txt files and upload it
into a specified Google Drive folder.

Auth expectations:
- A service account JSON is made available via GOOGLE_APPLICATION_CREDENTIALS (workflow writes the secret to a file).
- The Drive folder (target) must be shared with the service account email (client_email in the JSON) OR the service account must own the folder.
- Required APIs enabled in the GCP project: Google Drive API, Google Docs API.

Usage:
  python scripts/upload_to_drive.py --folder-id <DRIVE_FOLDER_ID>

Outputs:
  - Prints the created Google Doc URL and file id on success.
"""

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
]

def collect_text_files(pattern="output_*.txt"):
    files = sorted(glob.glob(pattern))
    return files

def aggregate_contents(files):
    parts = []
    for p in files:
        try:
            with open(p, "r", encoding="utf-8") as fh:
                txt = fh.read()
            parts.append(txt)
        except Exception as e:
            print(f"Warning: failed to read {p}: {e}", file=sys.stderr)
    if not parts:
        return ""
    # Separate documents with a couple of newlines
    return "\n\n".join(parts)

def create_google_doc(drive_service, name, folder_id):
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.document",
    }
    if folder_id:
        metadata["parents"] = [folder_id]
    file = drive_service.files().create(body=metadata, fields="id").execute()
    return file.get("id")

def insert_text_into_doc(docs_service, document_id, text):
    # Insert text at index 1 (after the initial structural element)
    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": text,
            }
        }
    ]
    docs_service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()

def get_service_account_email_from_keyfile(keyfile_path):
    try:
        with open(keyfile_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("client_email")
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder-id", required=True, help="Google Drive folder ID to upload the doc into")
    parser.add_argument("--pattern", default="output_*.txt", help="Glob pattern for scraped files")
    args = parser.parse_args()

    keyfile = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not keyfile or not Path(keyfile).exists():
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS not set or file not found.", file=sys.stderr)
        sys.exit(2)

    files = collect_text_files(args.pattern)
    if not files:
        print("ERROR: no scraped files matching pattern found. Nothing to upload.", file=sys.stderr)
        sys.exit(0)

    aggregated = aggregate_contents(files)
    if not aggregated:
        print("ERROR: aggregated content is empty.", file=sys.stderr)
        sys.exit(0)

    # Build credentials and API clients
    creds = service_account.Credentials.from_service_account_file(keyfile, scopes=SCOPES)
    drive_service = build("drive", "v3", credentials=creds)
    docs_service = build("docs", "v1", credentials=creds)

    # Build filename: output_YYYYMMDD.docx
    timestamp = time.strftime("%Y%m%d")
    filename = f"output_{timestamp}.docx"

    try:
        doc_id = create_google_doc(drive_service, filename, args.folder_id)
        insert_text_into_doc(docs_service, doc_id, aggregated)
    except HttpError as e:
        print("Google API error:", e, file=sys.stderr)
        # Helpful hint when permission problems happen
        sa_email = get_service_account_email_from_keyfile(keyfile)
        if sa_email:
            print(f"\nHint: ensure the folder {args.folder_id} is shared with the service account: {sa_email}", file=sys.stderr)
        raise

    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print("Created Google Doc:", doc_url)
    print("File ID:", doc_id)

if __name__ == "__main__":
    main()
