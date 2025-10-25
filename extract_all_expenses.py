#!/usr/bin/env python3
"""
Simple script to extract ALL expense messages (no date filter)
and save them to the database
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sms_extractor import SMSExtractor
from expense_parser import ExpenseParser
from database import ExpenseDatabase
from categorizer import ExpenseCategorizer

print("=" * 80)
print("Extracting ALL expense messages from Messages database")
print("=" * 80)

# Initialize
extractor = SMSExtractor()
parser = ExpenseParser()
db = ExpenseDatabase('data/expenses.db')
categorizer = ExpenseCategorizer(use_ai=True  # Enable AI categorization)  # Disable AI for testing

# Step 1: Extract messages (NO DATE FILTER)
print("\n[1/4] Extracting ALL SMS messages...")
try:
    messages_df = extractor.extract_messages()  # No start/end date
    print(f"  ✓ Found {len(messages_df)} potential expense messages")

    if len(messages_df) > 0:
        print(f"\n  Sample messages:")
        for idx, row in messages_df.head(5).iterrows():
            preview = row['text'][:80].replace('\n', ' ')
            print(f"  - [{row['date']}] {preview}...")
except Exception as e:
    print(f"  ✗ Error extracting messages: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if messages_df.empty:
    print("\n⚠ No messages found!")
    print("\nPossible issues:")
    print("1. Messages database not accessible")
    print("2. No messages match the financial keywords")
    print("3. All messages are marked as 'from me' (sent by you)")
    print("\nRun 'python test_arabic.py' to diagnose the issue")
    sys.exit(1)

# Step 2: Parse expenses
print("\n[2/4] Parsing expense data...")
try:
    expenses = []
    for idx, row in messages_df.iterrows():
        parsed = parser.parse_message(row['text'])
        if parsed:
            parsed['date'] = row['date']
            parsed['sender'] = row['sender']
            parsed['raw_message'] = row['text']
            expenses.append(parsed)

    print(f"  ✓ Parsed {len(expenses)} out of {len(messages_df)} messages")

    if len(expenses) > 0:
        total = sum(e['amount'] for e in expenses)
        print(f"  ✓ Total amount: ${total:,.2f}")

        print(f"\n  Sample parsed expenses:")
        for exp in expenses[:5]:
            print(f"  - {exp['merchant']}: ${exp['amount']:.2f}")
except Exception as e:
    print(f"  ✗ Error parsing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if not expenses:
    print("\n⚠ No expenses could be parsed!")
    print("\nThe messages were found but couldn't be parsed.")
    print("This means the regex patterns don't match your SMS format.")
    print("\nShowing first few messages that failed to parse:")
    for idx, row in messages_df.head(3).iterrows():
        print(f"\n{row['text'][:200]}")
    sys.exit(1)

# Step 3: Categorize
print("\n[3/4] Categorizing expenses...")
try:
    for exp in expenses:
        result = categorizer.categorize_expense(
            merchant=exp['merchant'],
            amount=exp['amount'],
            raw_message=exp.get('raw_message', '')
        )
        exp['category'] = result['category']
        exp['category_confidence'] = result.get('confidence', 0.5)
        exp['category_method'] = result.get('method', 'rule-based')

    print(f"  ✓ Categorized {len(expenses)} expenses")
except Exception as e:
    print(f"  ✗ Error categorizing: {e}")
    import traceback
    traceback.print_exc()
    # Continue anyway with default category
    for exp in expenses:
        if 'category' not in exp:
            exp['category'] = 'Uncategorized'

# Step 4: Save to database
print("\n[4/4] Saving to database...")
try:
    saved_count = 0
    for exp in expenses:
        from datetime import datetime

        # Parse date
        if isinstance(exp['date'], str):
            date_obj = datetime.strptime(exp['date'], '%Y-%m-%d %H:%M:%S')
        else:
            date_obj = exp['date']

        # Create expense dict for database
        expense_dict = {
            'date': date_obj.strftime('%Y-%m-%d %H:%M:%S') if isinstance(date_obj, datetime) else str(date_obj),
            'amount': exp['amount'],
            'merchant': exp['merchant'],
            'category': exp.get('category', 'Uncategorized'),
            'sender': exp.get('sender', ''),
            'raw_message': exp['raw_message'],
            'notes': ''
        }

        db.add_expense(expense_dict)
        saved_count += 1

    print(f"  ✓ Saved {saved_count} expenses to database")

    # Get stats
    stats = db.get_statistics()
    print(f"\n📊 Database Summary:")
    print(f"  Total expenses: {stats['total_expenses']}")
    print(f"  Total amount: ${stats['total_amount']:,.2f}")
    print(f"  Average: ${stats['average_expense']:.2f}")

    if stats['by_category']:
        print(f"\n  Top categories:")
        for cat, amount in list(stats['by_category'].items())[:5]:
            print(f"    - {cat}: ${amount:,.2f}")

except Exception as e:
    print(f"  ✗ Error saving to database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✓ Complete! You can now run the dashboard:")
print("  streamlit run src/dashboard.py")
print("=" * 80)
