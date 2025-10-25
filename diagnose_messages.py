#!/usr/bin/env python3
"""
Diagnostic script to check Messages database
Run this on your Mac to see what's in the database
"""
import sqlite3
import os
from datetime import datetime, timedelta

# Messages database path
DB_PATH = os.path.expanduser("~/Library/Messages/chat.db")

print(f"Checking Messages database at: {DB_PATH}")
print(f"Database exists: {os.path.exists(DB_PATH)}\n")

if not os.path.exists(DB_PATH):
    print("ERROR: Messages database not found!")
    print("Make sure you:")
    print("1. Are running this on a Mac")
    print("2. Have Messages synced from iPhone")
    print("3. Have granted Full Disk Access to Terminal")
    exit(1)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check total messages
    cursor.execute("SELECT COUNT(*) FROM message")
    total = cursor.fetchone()[0]
    print(f"Total messages in database: {total:,}")

    # Check date range - Messages uses Mac epoch (2001-01-01)
    cursor.execute("""
        SELECT
            MIN(date),
            MAX(date)
        FROM message
    """)
    min_date, max_date = cursor.fetchone()

    if min_date and max_date:
        # Convert from Mac epoch to Unix epoch
        mac_epoch = datetime(2001, 1, 1)
        min_dt = mac_epoch + timedelta(seconds=min_date/1e9)
        max_dt = mac_epoch + timedelta(seconds=max_date/1e9)

        print(f"Date range: {min_dt.strftime('%Y-%m-%d')} to {max_dt.strftime('%Y-%m-%d')}")

    # Check for messages with text
    cursor.execute("""
        SELECT COUNT(*)
        FROM message
        WHERE text IS NOT NULL AND text != ''
    """)
    with_text = cursor.fetchone()[0]
    print(f"Messages with text: {with_text:,}")

    # Check for potential bank/payment messages
    keywords = ['paid', 'spent', 'purchase', 'transaction', 'debited', 'credited',
                'bank', 'card', 'payment', 'balance', 'INR', 'Rs', '$']

    for keyword in keywords[:5]:  # Check first 5 keywords
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM message
            WHERE text LIKE '%{keyword}%'
        """)
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Messages containing '{keyword}': {count:,}")

    # Show sample recent messages
    print("\n=== Sample Recent Messages ===")
    cursor.execute("""
        SELECT
            datetime(date/1000000000 + 978307200, 'unixepoch') as date,
            text
        FROM message
        WHERE text IS NOT NULL AND text != ''
        ORDER BY date DESC
        LIMIT 5
    """)

    for date, text in cursor.fetchall():
        preview = text[:100] + "..." if len(text) > 100 else text
        print(f"\n[{date}]")
        print(f"  {preview}")

    # Check table structure
    print("\n=== Database Schema Info ===")
    cursor.execute("PRAGMA table_info(message)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Available columns: {', '.join(columns[:10])}...")

    conn.close()

except sqlite3.Error as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
