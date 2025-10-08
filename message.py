#!/usr/bin/env python3
"""
slack_message_sender.py
Sends messages to Slack channels using the chat.postMessage API endpoint.
Based on the structure from getuserinfo.py and the provided API request details.

Usage:
    python message.py "Hello, this is a test message!" --channel D09JFMEFZL3

Environment Variables Required:
    SLACK_COOKIE - Cookie string from browser session
    SLACK_XOXC - Slack token (xoxc-...)
    TO_USER - Default channel ID (optional, can be overridden with --channel)
"""

import os
import json
import sys
import uuid
import time
import requests
import argparse
import sqlite3
from dotenv import load_dotenv

load_dotenv()  # loads .env into environment

# Ensure stdout can print Unicode symbols on Windows consoles
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Environment variables
COOKIE = os.getenv("SLACK_COOKIE", "").strip()
XOXC_TOKEN = os.getenv("SLACK_XOXC", "").strip()
SQLITE_PATH = os.getenv("SQLITE_PATH", "people.db").strip()



# olegdomanov8@gmail.com
# REQUEST_URL = (
#     "https://shopifypartners.slack.com/api/chat.postMessage"
#     "?_x_id=d2d21f07-1759799665.874"
#     "&_x_csid=wZowavYWxo0"
#     "&slack_route=T4BB7S7HP"
#     "&_x_version_ts=1759776465"
#     "&_x_frontend_build_type=current"
#     "&_x_desktop_ia=4"
#     "&_x_gantry=true"
#     "&fp=3d"
#     "&_x_num_retries=0"
# )


# rusuland9@gmail.com
REQUEST_URL = (
    "https://shopifypartners.slack.com/api/chat.postMessage"
    "?_x_id=8875ce36-1759870645.754"
    "&_x_csid=9YrUsgKetCo"
    "&slack_route=T4BB7S7HP"
    "&_x_version_ts=1759863116"
    "&_x_frontend_build_type=current"
    "&_x_desktop_ia=4"
    "&_x_gantry=true"
    "&fp=13"
    "&_x_num_retries=0"
)


def build_session_from_cookie(cookie_header: str) -> requests.Session:
    """Build a requests session with cookies from the cookie header string."""
    s = requests.Session()
    # Parse the cookie string into name/value pairs and set in session cookiejar
    pairs = [p.strip() for p in cookie_header.split(";") if p.strip()]
    for p in pairs:
        if "=" in p:
            name, value = p.split("=", 1)
            # Set cookie for the slack domain
            s.cookies.set(name.strip(), value.strip(), domain="shopifypartners.slack.com")
    return s

def create_message_blocks(text: str) -> list:
    """Create Slack message blocks structure for rich text."""
    return [
        {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
            ]
        }
    ]

def send_message(session: requests.Session, message: str, channel: str, thread_ts: str = None) -> dict:
    """Send a message to a Slack channel."""
    
    # Generate unique IDs
    client_msg_id = str(uuid.uuid4())
    draft_id = str(uuid.uuid4())
    current_ts = str(int(time.time() * 1000))
    
    # Headers (from your request)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Origin": "https://app.slack.com",
        "Referer": "https://app.slack.com/client/T4BB7S7HP/",
        "Sec-CH-UA": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Priority": "u=1, i"
    }
    



    form_data = {
        "_x_id": f"3aad4449-{int(time.time())}.062",
        "_x_csid": "KI9fc-aj9RA",
        "slack_route": "T4BB7S7HP",
        "_x_version_ts": "1759865261",
        "_x_frontend_build_type": "current",
        "_x_desktop_ia": "4",
        "_x_gantry": "true",
        "fp": "13",
        "_x_num_retries": "0",
        "token": XOXC_TOKEN,
        "channel": channel,
        "ts": current_ts,
        "type": "message",
        "xArgs": json.dumps({"draft_id": draft_id}),
        "unfurl": "[]",
        "client_context_team_id": "T4BB7S7HP",
        "blocks": json.dumps(create_message_blocks(message)),
        "draft_id": draft_id,
        "include_channel_perm_error": "true",
        "client_msg_id": client_msg_id,
        "_x_reason": "webapp_message_send",
        "_x_mode": "online",
        "_x_sonic": "true",
        "_x_app_name": "client"
    }

    # #olegdomanov
    # form_data = {
    #     "_x_id": f"d2d21f07-{int(time.time())}.874",
    #     "_x_csid": "wZowavYWxo0",
    #     "slack_route": "T4BB7S7HP",
    #     "_x_version_ts": "1759776465",
    #     "_x_frontend_build_type": "current",
    #     "_x_desktop_ia": "4",
    #     "_x_gantry": "true",
    #     "fp": "3d",
    #     "_x_num_retries": "0",
    #     "token": XOXC_TOKEN,
    #     "channel": channel,
    #     "ts": current_ts,
    #     "type": "message",
    #     "xArgs": json.dumps({"draft_id": draft_id}),
    #     "unfurl": "[]",
    #     "client_context_team_id": "T4BB7S7HP",
    #     "blocks": json.dumps(create_message_blocks(message)),
    #     "draft_id": draft_id,
    #     "include_channel_perm_error": "true",
    #     "client_msg_id": client_msg_id,
    #     "_x_reason": "webapp_message_send",
    #     "_x_mode": "online",
    #     "_x_sonic": "true",
    #     "_x_app_name": "client"
    # }
    
    # Add thread_ts if replying to a thread
    if thread_ts:
        form_data["thread_ts"] = thread_ts
    
    # Convert to multipart form data
    files = {k: (None, v) for k, v in form_data.items()}
    
    print(f"Sending message to channel {channel}...")
    print(f"Message: {message}")
    
    try:
        response = session.post(REQUEST_URL, headers=headers, files=files, timeout=30)
        
        print(f"HTTP Status: {response.status_code}")
        
        # Check for HTML response (login page)
        if "text/html" in response.headers.get("Content-Type", ""):
            print("⚠️ Received HTML response. Your cookie/token may be invalid.")
            return {"error": "Authentication failed", "status_code": response.status_code}
        
        # Try to parse JSON response
        try:
            result = response.json()
            print("✅ Message sent successfully!")
            print("Response:", json.dumps(result, indent=2))
            return result
        except ValueError:
            # Response might be compressed or not JSON
            print("⚠️ Response not JSON format.")
            print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"Content-Encoding: {response.headers.get('Content-Encoding', 'none')}")
            
            # If it's a 200 status, consider it successful even if we can't parse JSON
            if response.status_code == 200:
                print("✅ Message likely sent successfully (HTTP 200)")
                return {"success": True, "status_code": response.status_code, "note": "Response format not JSON"}
            else:
                print("Raw response:")
                print(response.text)
                return {"error": "Invalid response format", "text": response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {"error": str(e)}

def get_all_user_ids(db_path: str) -> list:
    ids = []
    if not os.path.exists(db_path):
        return ids
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM people WHERE user_id IS NOT NULL AND user_id != ''")
        for row in cur.fetchall():
            uid = row[0]
            if uid:
                ids.append(uid)
    finally:
        conn.close()
    return ids

def read_message_from_file(file_path: str = "content.txt") -> str:
    """Read message content from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return "Hello"  # fallback if file is empty
            return content
    except FileNotFoundError:
        print(f"⚠️ File {file_path} not found. Using default message 'Hello'")
        return "Hello"
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}. Using default message 'Hello'")
        return "Hello"

def main():
    parser = argparse.ArgumentParser(description="Send a message to Slack")
    parser.add_argument("message", nargs="?", default="Hello", help="The message text to send (default: Hello)")
    parser.add_argument("--channel", "-c", help="Channel ID to send message to")
    parser.add_argument("--thread", "-t", help="Thread timestamp to reply to")
    
    args = parser.parse_args()
    
    # Read message from content.txt file
    message_text = read_message_from_file("content.txt")
    print(f"📄 Message loaded from content.txt: {message_text[:50]}{'...' if len(message_text) > 50 else ''}")
    
    # Validate required environment variables
    if not COOKIE or not XOXC_TOKEN:
        print("❌ ERROR: Please set SLACK_COOKIE and SLACK_XOXC in your .env file")
        print("\nRequired environment variables:")
        print("  SLACK_COOKIE - Cookie string from your browser session")
        print("  SLACK_XOXC - Your Slack token (xoxc-...)")
        print("  TO_USER - Default channel ID (optional)")
        sys.exit(1)
    
    # Build session
    session = build_session_from_cookie(COOKIE)
    
    # If a single channel is specified, send just once
    if args.channel:
        result = send_message(session, message_text, args.channel, args.thread)
        if "error" in result:
            print(f"❌ Failed to send message: {result['error']}")
            sys.exit(1)
        print("✅ Message sent successfully!")
        return

    # Otherwise, load all user_ids from SQLite and loop
    TO_USERS = get_all_user_ids(SQLITE_PATH)
    if not TO_USERS and TO_USER:
        TO_USERS = [TO_USER]
    if not TO_USERS:
        print("❌ No recipients found. Provide --channel or ensure people.db exists and is populated.")
        sys.exit(1)

    print(f"Found {len(TO_USERS)} recipient(s). Starting broadcast...")
    success = 0
    failure = 0
    for idx, uid in enumerate(TO_USERS, 1):
        result = send_message(session, message_text, uid, args.thread)
        if "error" in result:
            failure += 1
            print(f"[{idx}/{len(TO_USERS)}] ❌ {uid}: {result['error']}")
        else:
            success += 1
            print(f"[{idx}/{len(TO_USERS)}] ✅ {uid}")
        if idx < len(TO_USERS):
            time.sleep(0.8)
    print(f"Done. Success: {success}, Failures: {failure}")
    if failure:
        sys.exit(1)

if __name__ == "__main__":
    main()