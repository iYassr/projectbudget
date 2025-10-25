#!/usr/bin/env python3
"""
Update expenses database - only adds NEW expenses (no duplicates)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sms_extractor import SMSExtractor
from expense_parser import ExpenseParser
from database import ExpenseDatabase
from categorizer import ExpenseCategorizer
from datetime import datetime

print("=" * 80)
print("Updating Expenses Database (Duplicate-Safe)")
print("=" * 80)

# Initialize
extractor = SMSExtractor()
parser = ExpenseParser()
db = ExpenseDatabase('data/expenses.db')
categorizer = ExpenseCategorizer(use_ai=True  # Enable AI categorization)

# Get existing expenses to check for duplicates
print("\n[1/5] Checking existing expenses...")
import sqlite3
conn = sqlite3.connect('data/expenses.db')
cursor = conn.cursor()
cursor.execute("SELECT date, merchant, amount FROM expenses")
existing = set((row[0], row[1], row[2]) for row in cursor.fetchall())
conn.close()
print(f"  Found {len(existing):,} existing expenses")

# Extract messages
print("\n[2/5] Extracting SMS messages...")
messages_df = extractor.extract_messages()
print(f"  Extracted {len(messages_df):,} potential expense messages")

if messages_df.empty:
    print("\n⚠ No messages found!")
    sys.exit(1)

# Parse expenses
print("\n[3/5] Parsing expense data...")
expenses = []
for idx, row in messages_df.iterrows():
    parsed = parser.parse_message(row['text'])
    if parsed:
        parsed['date'] = row['date']
        parsed['sender'] = row['sender']
        parsed['raw_message'] = row['text']
        expenses.append(parsed)

print(f"  Parsed {len(expenses):,} expenses")

# Filter out duplicates
print("\n[4/5] Filtering duplicates...")
new_expenses = []
for exp in expenses:
    # Check if this exact expense already exists
    key = (exp['date'], exp['merchant'], exp['amount'])
    if key not in existing:
        new_expenses.append(exp)

duplicates_skipped = len(expenses) - len(new_expenses)
print(f"  New expenses to add: {len(new_expenses):,}")
print(f"  Duplicates skipped: {duplicates_skipped:,}")

if not new_expenses:
    print("\n✓ No new expenses to add - database is up to date!")
    sys.exit(0)

# Categorize and save new expenses
print("\n[5/5] Categorizing and saving new expenses...")
saved_count = 0
for exp in new_expenses:
    # Categorize
    result = categorizer.categorize_expense(
        merchant=exp['merchant'],
        amount=exp['amount'],
        raw_message=exp.get('raw_message', '')
    )
    exp['category'] = result['category']

    # Save
    expense_dict = {
        'date': exp['date'] if isinstance(exp['date'], str) else exp['date'].strftime('%Y-%m-%d %H:%M:%S'),
        'amount': exp['amount'],
        'merchant': exp['merchant'],
        'category': exp['category'],
        'currency': exp.get('currency', 'SAR'),
        'sender': exp.get('sender', ''),
        'raw_message': exp['raw_message'],
        'notes': ''
    }

    db.add_expense(expense_dict)
    saved_count += 1

print(f"  ✓ Saved {saved_count:,} new expenses")

# Show some of the new expenses
print("\n  Sample new expenses:")
for exp in new_expenses[:5]:
    print(f"  - {exp['date'][:10]} | {exp['merchant'][:30]:30} | ${exp['amount']:.2f}")

# Get updated stats
stats = db.get_statistics()
print(f"\n📊 Updated Database Summary:")
print(f"  Total expenses: {stats['total_expenses']:,}")
print(f"  Total amount: ${stats['total_amount']:,.2f}")

print("\n" + "=" * 80)
print("✓ Update complete! Refresh your dashboard to see new expenses.")
print("=" * 80)
