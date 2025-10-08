#!/usr/bin/env python3
"""
delete_channel.py
Delete messages from a specific Slack channel by fetching recent messages first.
"""

import os
import sys
import time
import requests
import argparse
from dotenv import load_dotenv

load_dotenv()

# Environment variables
COOKIE = os.getenv("SLACK_COOKIE", "").strip()
XOXC_TOKEN = os.getenv("SLACK_XOXC", "").strip()

def build_session_from_cookie(cookie_header: str) -> requests.Session:
    """Build a requests session with cookies from the cookie header string."""
    s = requests.Session()
    pairs = [p.strip() for p in cookie_header.split(";") if p.strip()]
    for p in pairs:
        if "=" in p:
            name, value = p.split("=", 1)
            s.cookies.set(name.strip(), value.strip(), domain="shopifypartners.slack.com")
    return s

def get_channel_messages(session: requests.Session, channel_id: str, limit: int = 100) -> list:
    """Get recent messages from a channel using conversations.history API."""
    
    url = "https://shopifypartners.slack.com/api/conversations.history"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Origin": "https://app.slack.com",
        "Referer": f"https://app.slack.com/client/T4BB7S7HP/{channel_id}",
    }
    
    form_data = {
        "token": XOXC_TOKEN,
        "channel": channel_id,
        "limit": str(limit),
        "inclusive": "true",
        "oldest": "0"
    }
    
    files = {k: (None, v) for k, v in form_data.items()}
    
    try:
        response = session.post(url, headers=headers, files=files, timeout=30)
        print(f"Fetching messages from {channel_id}... HTTP {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("ok") and "messages" in data:
                    messages = data["messages"]
                    print(f"Found {len(messages)} messages in channel")
                    return messages
                else:
                    print(f"API Error: {data.get('error', 'Unknown error')}")
            except ValueError:
                print("Failed to parse JSON response")
        else:
            print(f"HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"Request failed: {e}")
    
    return []

def delete_message(session: requests.Session, channel: str, ts: str) -> bool:
    """Delete a specific message."""
    
    url = "https://shopifypartners.slack.com/api/chat.delete"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Origin": "https://app.slack.com",
        "Referer": f"https://app.slack.com/client/T4BB7S7HP/{channel}",
    }
    
    form_data = {
        "token": XOXC_TOKEN,
        "channel": channel,
        "ts": ts
    }
    
    files = {k: (None, v) for k, v in form_data.items()}
    
    try:
        response = session.post(url, headers=headers, files=files, timeout=30)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("ok"):
                    return True
                else:
                    print(f"Delete failed: {data.get('error', 'Unknown error')}")
            except ValueError:
                # Even if we can't parse JSON, HTTP 200 might mean success
                return True
        else:
            print(f"HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"Delete request failed: {e}")
    
    return False

def read_channels_from_file(file_path: str = "channel.txt") -> list:
    """Read channel IDs from a text file."""
    channels = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                channel_id = line.strip()
                if channel_id and not channel_id.startswith('#'):
                    channels.append(channel_id)
    except FileNotFoundError:
        print(f"⚠️ File {file_path} not found")
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}")
    return channels

def main():
    parser = argparse.ArgumentParser(description="Delete messages from Slack channels")
    parser.add_argument("--channel", "-c", help="Single channel ID to delete messages from")
    parser.add_argument("--file", "-f", default="channel.txt", help="File containing channel IDs (default: channel.txt)")
    parser.add_argument("--limit", type=int, default=50, help="Number of recent messages to fetch and delete per channel")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between deletions in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    
    args = parser.parse_args()
    
    if not COOKIE or not XOXC_TOKEN:
        print("❌ ERROR: Please set SLACK_COOKIE and SLACK_XOXC in your .env file")
        sys.exit(1)
    
    session = build_session_from_cookie(COOKIE)
    
    # Determine which channels to process
    if args.channel:
        # Single channel mode
        channels = [args.channel]
        print(f"🎯 Single channel mode: {args.channel}")
    else:
        # Multiple channels from file
        channels = read_channels_from_file(args.file)
        if not channels:
            print(f"❌ No channels found in {args.file}")
            sys.exit(1)
        print(f"📁 Reading {len(channels)} channels from {args.file}")
    
    total_deleted = 0
    total_channels_processed = 0
    
    for channel_idx, channel_id in enumerate(channels, 1):
        print(f"\n🔍 [{channel_idx}/{len(channels)}] Processing channel {channel_id}...")
        
        messages = get_channel_messages(session, channel_id, args.limit)
        
        if not messages:
            print(f"  ⚠️ No messages found in {channel_id}")
            continue
        
        # Filter messages that can be deleted (all messages)
        deletable_messages = []
        for msg in messages:
            if msg.get("type") == "message" and "ts" in msg:
                # Include all messages (not just yours)
                if "user" in msg or "bot_id" in msg:
                    deletable_messages.append(msg)
        
        if not deletable_messages:
            print(f"  ⚠️ No deletable messages in {channel_id}")
            continue
        
        print(f"  📋 Found {len(deletable_messages)} deletable messages")
        
        if args.dry_run:
            print(f"  🔍 DRY RUN - Messages that would be deleted from {channel_id}:")
            for i, msg in enumerate(deletable_messages, 1):
                text = msg.get("text", "")[:50] + "..." if len(msg.get("text", "")) > 50 else msg.get("text", "")
                print(f"    {i}. {msg['ts']} - {text}")
            continue
        
        # Delete messages
        success_count = 0
        for i, msg in enumerate(deletable_messages, 1):
            ts = msg["ts"]
            text_preview = msg.get("text", "")[:30] + "..." if len(msg.get("text", "")) > 30 else msg.get("text", "")
            
            print(f"  [{i}/{len(deletable_messages)}] Deleting {ts} - {text_preview}")
            
            if delete_message(session, channel_id, ts):
                success_count += 1
                print(f"    ✅ Deleted successfully")
            else:
                print(f"    ❌ Failed to delete")
            
            if i < len(deletable_messages) and args.delay > 0:
                time.sleep(args.delay)
        
        print(f"  ✅ Channel {channel_id}: Deleted {success_count}/{len(deletable_messages)} messages")
        total_deleted += success_count
        total_channels_processed += 1
        
        # Delay between channels
        if channel_idx < len(channels) and args.delay > 0:
            time.sleep(args.delay)
    
    if not args.dry_run:
        print(f"\n🎉 BULK DELETION COMPLETE!")
        print(f"📊 Processed {total_channels_processed} channels")
        print(f"🗑️ Total messages deleted: {total_deleted}")
    else:
        print(f"\n🔍 DRY RUN COMPLETE!")
        print(f"📊 Would process {len(channels)} channels")

if __name__ == "__main__":
    main()
