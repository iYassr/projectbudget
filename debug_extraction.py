#!/usr/bin/env python3
"""
Debug why 2025 messages aren't being extracted
"""
import sqlite3
import os
from datetime import datetime

# Messages database path
DB_PATH = os.path.expanduser("~/Library/Messages/chat.db")

print("=" * 80)
print("Debugging SMS Extraction for 2025")
print("=" * 80)

if not os.path.exists(DB_PATH):
    print("ERROR: Messages database not found!")
    exit(1)

conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
cursor = conn.cursor()

# Check total messages in 2025
print("\n1. Total messages in 2025:")
cursor.execute("""
    SELECT COUNT(*)
    FROM message
    WHERE text IS NOT NULL
    AND date >= (strftime('%s', '2025-01-01') - strftime('%s', '2001-01-01')) * 1000000000
""")
total_2025 = cursor.fetchone()[0]
print(f"   Total messages with text: {total_2025:,}")

# Check for financial keywords in 2025
keywords = ['SAR', 'شراء', 'مبلغ', 'بطاقة', 'حوالة', 'purchase', 'amount']

print("\n2. Messages in 2025 containing financial keywords:")
for keyword in keywords:
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM message
        WHERE text LIKE '%{keyword}%'
        AND date >= (strftime('%s', '2025-01-01') - strftime('%s', '2001-01-01')) * 1000000000
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"   '{keyword}': {count:,}")

# Check if messages are marked as "from me"
print("\n3. Checking is_from_me flag (only messages NOT from you are extracted):")
cursor.execute("""
    SELECT is_from_me, COUNT(*)
    FROM message
    WHERE text LIKE '%SAR%'
    AND date >= (strftime('%s', '2025-01-01') - strftime('%s', '2001-01-01')) * 1000000000
    GROUP BY is_from_me
""")
for is_from_me, count in cursor.fetchall():
    sender = "FROM ME (sent by you - IGNORED)" if is_from_me else "TO ME (received - EXTRACTED)"
    print(f"   {sender}: {count:,}")

# Sample 2025 messages with SAR
print("\n4. Sample 2025 messages with 'SAR':")
cursor.execute("""
    SELECT
        datetime(date/1000000000 + 978307200, 'unixepoch') as date,
        is_from_me,
        substr(text, 1, 100) as preview
    FROM message
    WHERE text LIKE '%SAR%'
    AND date >= (strftime('%s', '2025-01-01') - strftime('%s', '2001-01-01')) * 1000000000
    ORDER BY date DESC
    LIMIT 10
""")

for date, is_from_me, preview in cursor.fetchall():
    from_me = "[SENT]" if is_from_me else "[RECV]"
    print(f"\n   {date} {from_me}")
    print(f"   {preview}...")

# Check specific Amazon message
print("\n5. Searching for the specific Amazon message you mentioned:")
cursor.execute("""
    SELECT
        datetime(date/1000000000 + 978307200, 'unixepoch') as date,
        is_from_me,
        text
    FROM message
    WHERE text LIKE '%Amazon SA%'
    AND text LIKE '%783.30%'
    LIMIT 1
""")

result = cursor.fetchone()
if result:
    date, is_from_me, text = result
    print(f"   Found! Date: {date}")
    print(f"   is_from_me: {is_from_me} ({'SENT - will be IGNORED' if is_from_me else 'RECEIVED - will be extracted'})")
    print(f"   Full text:\n{text}")
else:
    print("   ❌ Not found in Messages database!")

conn.close()

print("\n" + "=" * 80)
print("If messages show as [SENT], they're being filtered out because")
print("the extractor only gets RECEIVED messages (is_from_me=0)")
print("=" * 80)
