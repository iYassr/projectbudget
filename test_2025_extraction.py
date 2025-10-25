#!/usr/bin/env python3
"""
Test extraction and parsing of 2025 messages
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sms_extractor import SMSExtractor
from expense_parser import ExpenseParser

print("=" * 80)
print("Testing 2025 Message Extraction & Parsing")
print("=" * 80)

# Extract messages
extractor = SMSExtractor()
parser = ExpenseParser()

print("\n[1] Extracting ALL messages...")
all_messages = extractor.extract_messages()
print(f"  Total extracted: {all_messages:,}")

# Filter to 2025
import pandas as pd
all_messages['date'] = pd.to_datetime(all_messages['date'])
messages_2025 = all_messages[all_messages['date'].dt.year == 2025]

print(f"\n[2] Messages from 2025:")
print(f"  Count: {len(messages_2025):,}")

if len(messages_2025) == 0:
    print("\n  ❌ No 2025 messages extracted! This is the problem.")
    print("  The extractor is finding 19 2025 messages in the database,")
    print("  but they're not matching the financial keywords.")
else:
    print(f"\n  Sample 2025 messages:")
    for idx, row in messages_2025.head(10).iterrows():
        preview = row['text'][:60].replace('\n', ' ')
        print(f"    {row['date']} | {preview}...")

    # Try parsing them
    print(f"\n[3] Parsing 2025 messages...")
    parsed_count = 0
    failed_count = 0

    parsed_list = []

    for idx, row in messages_2025.iterrows():
        result = parser.parse_message(row['text'])
        if result:
            parsed_count += 1
            parsed_list.append({
                'date': row['date'],
                'merchant': result['merchant'],
                'amount': result['amount']
            })
        else:
            failed_count += 1
            if failed_count <= 3:  # Show first 3 failures
                print(f"\n  ✗ Failed to parse:")
                print(f"    {row['text'][:150]}")

    print(f"\n  ✓ Successfully parsed: {parsed_count}/{len(messages_2025)}")
    print(f"  ✗ Failed to parse: {failed_count}/{len(messages_2025)}")

    if parsed_list:
        print(f"\n  Parsed expenses:")
        for p in parsed_list[:10]:
            print(f"    {p['date']} | {p['merchant'][:30]:30} | ${p['amount']:.2f}")

print("\n" + "=" * 80)
