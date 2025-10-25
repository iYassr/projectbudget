#!/usr/bin/env python3
"""
Show ALL 2025 messages to understand what we're missing
"""
import sqlite3
import os

DB_PATH = os.path.expanduser("~/Library/Messages/chat.db")

print("=" * 80)
print("ALL 2025 Messages from Messages Database")
print("=" * 80)

conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
cursor = conn.cursor()

# Get ALL 2025 messages (not from you)
cursor.execute("""
    SELECT
        datetime(date/1000000000 + 978307200, 'unixepoch') as date,
        substr(text, 1, 100) as preview
    FROM message
    WHERE text IS NOT NULL
    AND is_from_me = 0
    AND date >= (strftime('%s', '2025-01-01') - strftime('%s', '2001-01-01')) * 1000000000
    ORDER BY date DESC
""")

messages = cursor.fetchall()
total = len(messages)

print(f"\nTotal 2025 messages (received, not sent): {total:,}")
print("\nFirst 50 messages:")
print("-" * 80)

for i, (date, preview) in enumerate(messages[:50], 1):
    # Clean up preview
    preview = preview.replace('\n', ' | ')
    print(f"{i:3}. {date} | {preview}")

# Group by common words
print("\n" + "=" * 80)
print("Looking for common patterns in ALL 2025 messages...")
print("=" * 80)

# Check various patterns
patterns_to_check = [
    ('Contains numbers', r'\d'),
    ('Has SAR', 'SAR'),
    ('Has ريال', 'ريال'),
    ('Has شراء', 'شراء'),
    ('Has مبلغ', 'مبلغ'),
    ('Has بطاقة', 'بطاقة'),
    ('Has "card"', 'card'),
    ('Has "purchase"', 'purchase'),
    ('Has "amount"', 'amount'),
]

cursor.execute("""
    SELECT text
    FROM message
    WHERE text IS NOT NULL
    AND is_from_me = 0
    AND date >= (strftime('%s', '2025-01-01') - strftime('%s', '2001-01-01')) * 1000000000
""")

all_texts = [row[0] for row in cursor.fetchall()]

for pattern_name, pattern in patterns_to_check:
    count = sum(1 for text in all_texts if pattern in text)
    print(f"{pattern_name:25}: {count:4} messages ({count*100//total if total > 0 else 0}%)")

conn.close()

print("\n" + "=" * 80)
print(f"If you have 200+ expense messages but only {total} are shown,")
print("they might be marked as 'sent by you' (is_from_me=1)")
print("=" * 80)
