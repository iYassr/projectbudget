#!/usr/bin/env python3
"""
Extract expenses from imessage-exporter TXT export
"""
import os
import sys
import re
from datetime import datetime
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from expense_parser import ExpenseParser
from database import ExpenseDatabase
from categorizer import ExpenseCategorizer

# Path to TXT export folder
EXPORT_PATH = os.path.expanduser("~/messages_export")

print("=" * 80)
print("Extract Expenses from iMessage TXT Export")
print("=" * 80)

if not os.path.exists(EXPORT_PATH):
    print(f"\n❌ Export folder not found at: {EXPORT_PATH}")
    print("\nPlease export your messages first:")
    print("  imessage-exporter -f txt -o ~/messages_export --start-date 2022-01-01")
    sys.exit(1)

print(f"\n[1/5] Scanning export folder...")
print(f"  Path: {EXPORT_PATH}")

# Find all TXT files
txt_files = list(Path(EXPORT_PATH).rglob("*.txt"))
print(f"  Found {len(txt_files):,} conversation files")

if not txt_files:
    print("\n  ❌ No .txt files found in export folder!")
    sys.exit(1)

# Financial keywords
FINANCIAL_KEYWORDS = [
    'SAR', 'ريال', 'شراء', 'مبلغ', 'بطاقة', 'حوالة', 'رصيد',
    'purchase', 'amount', 'card', 'visa', 'transfer', 'balance',
    'SAIB', 'RJHI', 'مدى', 'فيزا', 'Online Purchases', 'POS Purchases'
]

print(f"\n[2/5] Extracting messages from TXT files...")

messages = []
total_lines = 0

# Pattern to match message format in TXT export
# Typically: [Date] Sender: Message text
# or just message text with timestamps

for txt_file in txt_files:
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            file_lines = f.readlines()

        i = 0
        while i < len(file_lines):
            line = file_lines[i].strip()
            total_lines += 1

            # Look for date line: "Oct 25, 2025  8:14:08 PM"
            date_match = re.match(r'([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)', line)

            if date_match:
                date_str = date_match.group(1)

                # Convert to standard format
                try:
                    dt = datetime.strptime(date_str, '%b %d, %Y %I:%M:%S %p')
                    standard_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    i += 1
                    continue

                # Next line should be sender
                i += 1
                if i >= len(file_lines):
                    break

                sender = file_lines[i].strip()

                # Skip if sent by "Me"
                if sender == "Me":
                    i += 1
                    continue

                # Collect message lines
                i += 1
                message_lines = []

                while i < len(file_lines):
                    next_line = file_lines[i].strip()

                    # Stop if we hit another date or separator
                    if re.match(r'[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}', next_line):
                        break
                    if next_line.startswith('Tapbacks:') or next_line.startswith('==>'):
                        break
                    if next_line.startswith('(Read by you'):
                        i += 1
                        continue

                    if next_line:
                        message_lines.append(next_line)

                    i += 1

                if message_lines:
                    msg_text = '\n'.join(message_lines)

                    # Check for financial keywords
                    if any(kw.lower() in msg_text.lower() for kw in FINANCIAL_KEYWORDS):
                        messages.append({
                            'text': msg_text,
                            'date': standard_date,
                            'sender': sender
                        })
            else:
                i += 1

    except Exception as e:
        print(f"  ⚠ Error reading {txt_file.name}: {e}")
        continue

print(f"  Processed {total_lines:,} lines")
print(f"  Found {len(messages):,} potential expense messages")

if not messages:
    print("\n  ❌ No financial messages found!")
    print("  The TXT format might be different than expected.")
    print("  Please share a sample of one .txt file for debugging.")
    sys.exit(1)

# Sample messages
print(f"\n  Sample messages:")
for msg in messages[:5]:
    preview = msg['text'][:80].replace('\n', ' ')
    print(f"    {msg['date']} | {preview}...")

# Parse expenses
print(f"\n[3/5] Parsing expenses...")
parser = ExpenseParser()
expenses = []

for msg in messages:
    result = parser.parse_message(msg['text'])
    if result:
        result['date'] = msg['date']
        result['sender'] = msg['sender']
        result['raw_message'] = msg['text']
        expenses.append(result)

parsed_rate = len(expenses) / len(messages) * 100 if messages else 0
print(f"  ✓ Parsed {len(expenses):,} expenses ({parsed_rate:.1f}% success rate)")

if len(expenses) > 0:
    total = sum(e['amount'] for e in expenses)
    print(f"  ✓ Total amount: ${total:,.2f}")

if not expenses:
    print("\n  ⚠ No expenses could be parsed!")
    print("  Showing first 3 messages that failed:")
    for msg in messages[:3]:
        print(f"\n  Date: {msg['date']}")
        print(f"  Text: {msg['text'][:200]}")
    sys.exit(0)

# Categorize
print(f"\n[4/5] Categorizing...")
categorizer = ExpenseCategorizer(use_ai=False)

for exp in expenses:
    result = categorizer.categorize_expense(
        merchant=exp['merchant'],
        amount=exp['amount'],
        raw_message=exp.get('raw_message', '')
    )
    exp['category'] = result['category']

print(f"  ✓ Categorized {len(expenses):,} expenses")

# Save to database
print(f"\n[5/5] Saving to database...")
db = ExpenseDatabase('data/expenses.db')

# Check for existing
import sqlite3
conn = sqlite3.connect('data/expenses.db')
cursor = conn.cursor()
cursor.execute("SELECT date, merchant, amount FROM expenses")
existing = set((row[0], row[1], row[2]) for row in cursor.fetchall())
conn.close()

new_expenses = []
for exp in expenses:
    key = (exp['date'], exp['merchant'], exp['amount'])
    if key not in existing:
        new_expenses.append(exp)

print(f"  New expenses: {len(new_expenses):,}")
print(f"  Duplicates skipped: {len(expenses) - len(new_expenses):,}")

if new_expenses:
    saved = 0
    for exp in new_expenses:
        expense_dict = {
            'date': exp['date'],
            'amount': exp['amount'],
            'merchant': exp['merchant'],
            'category': exp.get('category', 'Uncategorized'),
            'currency': exp.get('currency', 'SAR'),
            'sender': exp.get('sender', ''),
            'raw_message': exp['raw_message'],
            'notes': ''
        }
        db.add_expense(expense_dict)
        saved += 1

    print(f"  ✓ Saved {saved:,} new expenses")

# Stats
stats = db.get_statistics()
print(f"\n📊 Database Summary:")
print(f"  Total expenses: {stats['total_expenses']:,}")
print(f"  Total amount: ${stats['total_amount']:,.2f}")

print("\n" + "=" * 80)
print("✓ Complete! Refresh your dashboard.")
print("=" * 80)
