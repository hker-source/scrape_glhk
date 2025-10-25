#!/usr/bin/env python3
"""
Send aggregated scraped text via Gmail API (email body contains the aggregated text).

Uses these environment variables (set as GitHub secrets in the workflow):
- GMAIL_CLIENT_ID
- GMAIL_CLIENT_SECRET
- GMAIL_REFRESH_TOKEN
- SENDER_EMAIL            (email address to send from; also used as default recipient)
- RECIPIENT_EMAIL (optional, defaults to SENDER_EMAIL)

This script:
- Finds output_*.txt files
- Concatenates them with double newlines between entries
- Exchanges the refresh token for an access token
- Sends the email via Gmail API users.messages.send
"""
import os
import sys
import glob
import json
import time
import base64
import requests
from email.mime.text import MIMEText

GMAIL_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

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
    return "\n\n".join(parts)

def get_access_token(client_id, client_secret, refresh_token):
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    resp = requests.post(GMAIL_TOKEN_URL, data=data, timeout=30)
    try:
        resp.raise_for_status()
    except Exception as e:
        print("Failed to exchange refresh token:", resp.status_code, resp.text, file=sys.stderr)
        raise
    token = resp.json()
    return token.get("access_token"), token

def build_raw_message(sender, to, subject, body_text):
    msg = MIMEText(body_text, _subtype="plain", _charset="utf-8")
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return raw

def send_message(access_token, raw_message):
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    body = {"raw": raw_message}
    resp = requests.post(GMAIL_SEND_URL, headers=headers, json=body, timeout=30)
    try:
        resp.raise_for_status()
    except Exception:
        print("Error sending email:", resp.status_code, resp.text, file=sys.stderr)
        raise
    return resp.json()

def main():
    client_id = os.environ.get("GMAIL_CLIENT_ID")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET")
    refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN")
    sender = os.environ.get("SENDER_EMAIL")
    recipient = os.environ.get("RECIPIENT_EMAIL", sender)

    missing = [name for name, val in (
        ("GMAIL_CLIENT_ID", client_id),
        ("GMAIL_CLIENT_SECRET", client_secret),
        ("GMAIL_REFRESH_TOKEN", refresh_token),
        ("SENDER_EMAIL", sender),
    ) if not val]
    if missing:
        print("ERROR: missing required environment variables:", ", ".join(missing), file=sys.stderr)
        sys.exit(2)

    files = collect_text_files()
    if not files:
        print("ERROR: no output_*.txt files found to send. Exiting.", file=sys.stderr)
        sys.exit(0)

    aggregated = aggregate_contents(files)
    if not aggregated.strip():
        print("ERROR: aggregated text is empty. Nothing to send.", file=sys.stderr)
        sys.exit(0)

    print(f"Found {len(files)} files, total bytes: {len(aggregated.encode('utf-8'))}")

    access_token, token_resp = get_access_token(client_id, client_secret, refresh_token)
    if not access_token:
        print("ERROR: access_token not received from token endpoint:", token_resp, file=sys.stderr)
        sys.exit(2)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    subject = f"Scraped results — {timestamp}"

    raw = build_raw_message(sender, recipient, subject, aggregated)

    print("Sending email...")
    resp = send_message(access_token, raw)
    print("Email sent. Response:")
    print(json.dumps(resp, indent=2))

if __name__ == "__main__":
    main()
