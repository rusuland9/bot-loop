#!/usr/bin/env python3
"""
slack_people_from_env.py
Reads SLACK_COOKIE and SLACK_XOXC from .env and sends the same
POST request to the Slack internal endpoint you captured.

Produces:
 - people-info.json  (if JSON returned)
 - slack_people_raw.txt       (if non-JSON text returned)
 - people-info.html (if HTML returned, e.g. login)
"""

import os
import sys
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()  # loads .env into environment

# Ensure stdout can print Unicode symbols (e.g., checkmarks, warning signs) on Windows consoles
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

COOKIE = os.getenv("SLACK_COOKIE", "").strip()
XOXC_TOKEN = os.getenv("SLACK_XOXC", "").strip()
SQLITE_PATH = os.getenv("SQLITE_PATH", "people.db").strip()

# Allow DATABASE_URL style as well: sqlite:///people.db
db_url = os.getenv("DATABASE_URL", "").strip()
if db_url.startswith("sqlite:///"):
    SQLITE_PATH = db_url.replace("sqlite:///", "", 1)

# Pagination controls via environment
PAGE_START = int(os.getenv("PAGE_START", "1").strip() or 1)
MAX_PAGES = int(os.getenv("MAX_PAGES", "0").strip() or 0)  # 0 means unlimited until empty page

def persist_people_to_sqlite(payload: dict, db_path: str) -> None:
    items = payload.get("items", [])
    if not isinstance(items, list):
        return

    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS people (
              user_id TEXT PRIMARY KEY,
              username TEXT,
              real_name TEXT,
              display_name TEXT,
              email TEXT,
              team_id TEXT,
              image_192 TEXT,
              image_512 TEXT
            )
            """
        )

        upsert_sql = (
            "INSERT INTO people (user_id, username, real_name, display_name, email, team_id, image_192, image_512) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET "
            "username=excluded.username, real_name=excluded.real_name, display_name=excluded.display_name, "
            "email=excluded.email, team_id=excluded.team_id, image_192=excluded.image_192, image_512=excluded.image_512"
        )

        rows = []
        for item in items:
            user_id = item.get("id", "")
            username = item.get("username", "")
            profile = item.get("profile", {}) or {}
            real_name = profile.get("real_name") or ""
            display_name = profile.get("display_name") or ""
            email = profile.get("email") or ""
            team_id = profile.get("team") or ""
            image_192 = profile.get("image_192") or profile.get("image_72") or ""
            image_512 = profile.get("image_512") or ""
            if not user_id:
                continue
            rows.append((user_id, username, real_name, display_name, email, team_id, image_192, image_512))

        if rows:
            cursor.executemany(upsert_sql, rows)
        connection.commit()
    finally:
        connection.close()

if not COOKIE or not XOXC_TOKEN:
    print("ERROR: please set SLACK_COOKIE and SLACK_XOXC in your .env file")
    sys.exit(1)

REQUEST_URL = (
    "https://shopifypartners.slack.com/api/search.modules.people"
    "?_x_id=d2d21f07-1759804324.347"
    "&_x_csid=YMO1R_UnG-U"
    "&slack_route=T4BB7S7HP"
    "&_x_version_ts=1759776465"
    "&_x_frontend_build_type=current"
    "&_x_desktop_ia=4"
    "&_x_gantry=true"
    "&fp=3d"
    "&_x_num_retries=0"
)

FORM_FIELDS = {
    "module": "people",
    "query": "",
    "page": "120",
    "client_req_id": "dda9beeb-7dfd-4dd1-a4b8-825ee2ab0266",
    "browse_session_id": "dfea5e0c-b678-4081-92d8-519375ca3612",
    "extracts": "0",
    "highlight": "0",
    "extra_message_data": "1",
    "no_user_profile": "1",
    "count": "100",
    "file_title_only": "false",
    "query_rewrite_disabled": "false",
    "include_files_shares": "1",
    "browse": "standard",
    "search_context": "desktop_people_browser",
    "max_filter_suggestions": "10",
    "sort": "name",
    "sort_dir": "desc",
    "hide_deactivated_users": "1",
    "custom_fields": "{}",
    "_x_reason": "browser-query",
    "_x_mode": "online",
    "_x_sonic": "true",
    "_x_app_name": "client",
}

def build_session_from_cookie(cookie_header: str) -> requests.Session:
    s = requests.Session()
    # parse the cookie string into name/value pairs and set in session cookiejar
    pairs = [p.strip() for p in cookie_header.split(";") if p.strip()]
    for p in pairs:
        if "=" in p:
            name, value = p.split("=", 1)
            # set cookie for the slack domain
            s.cookies.set(name.strip(), value.strip(), domain="shopifypartners.slack.com")
    return s

def main():
    s = build_session_from_cookie(COOKIE)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "ja,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7,zh;q=0.6,id;q=0.5,de;q=0.4",
        "Origin": "https://app.slack.com",
        "Referer": "https://app.slack.com/client/T4BB7S7HP/people",
        # client-hint headers (optional)
        "Sec-CH-UA": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "Sec-CH-UA-Platform": '"Windows"',
    }

    current_page = PAGE_START
    total_items = 0
    pages_ok = 0

    # Keep requesting pages until no items are returned, or MAX_PAGES (if >0) is reached
    while True:
        # build multipart fields. Using requests `files` with (None, value) sends form-data
        files = {k: (None, v) for k, v in FORM_FIELDS.items()}
        files["token"] = (None, XOXC_TOKEN)
        files["page"] = (None, str(current_page))

        print(f"Sending request for page {current_page}...")
        resp = s.post(REQUEST_URL, headers=headers, files=files, timeout=30, allow_redirects=True)

        print("HTTP", resp.status_code)
        ct = resp.headers.get("Content-Type", "")
        text = resp.text

        # detect HTML/login
        if "text/html" in ct or "<!doctype html" in text.lower() or "login" in resp.url.lower():
            print("⚠️ Received HTML (login page or redirect). Your cookie/token may be invalid.")
            with open("people-info.html", "w", encoding="utf-8") as f:
                f.write(text)
            print("Saved people-info.html for inspection.")
            break

        # try parse JSON
        try:
            j = resp.json()
            print(j)
        except ValueError:
            print("⚠️ Response not JSON. Saving raw text.")
            with open("slack_people_raw.txt", "w", encoding="utf-8") as f:
                f.write(text)
            print("Saved slack_people_raw.txt")
            break

        items = j.get("items", []) if isinstance(j, dict) else []
        if not items:
            print("No items returned; stopping.")
            break

        # Persist this page immediately; if success, advance to next page
        try:
            persist_people_to_sqlite({"items": items}, SQLITE_PATH)
            pages_ok += 1
            total_items += len(items)
            print(f"✅ Page {current_page} upserted: {len(items)} users (total {total_items})")
        except Exception as e:
            print(f"⚠️ Failed to save page {current_page} to SQLite: {e}")
            break

        current_page += 1
        if MAX_PAGES > 0 and pages_ok >= MAX_PAGES:
            print("Reached MAX_PAGES limit; stopping.")
            break

    print(f"Done. Pages saved: {pages_ok}, total users upserted: {total_items}")

if __name__ == "__main__":
    main()
