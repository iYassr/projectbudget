#!/usr/bin/env python3
"""
Test script to verify Arabic SMS extraction and parsing
"""
from src.sms_extractor import SMSExtractor
from src.expense_parser import ExpenseParser

# Your actual SMS samples from the diagnostic output
test_messages = [
    "شراء\nبطاقة:9206;مدى-ابل باي\nمبلغ:SAR 114.38\nلدى:SASCO Qen\nفي:25-10-26 23:13",
    "حوالة محلية واردة\nعبر:SAIB\nمبلغ:SAR 10000\nالى:3057\nمن:YASSER ABDULRAHMAN ALDOSARI\nمن:3001\nفي:25-10-2",
    "Online Purchases:\nVISA card:**4681 (Apple Pay)\nAmount:139.40 SAR\nBalance:129.06\nAt:Keeta\nA/C:**7311",
    "شراء\nبطاقة:9206;مدى-ابل باي\nمبلغ:SAR 2\nلدى:COMPANY N\nفي:25-10-24 21:41",
]

print("Testing Arabic SMS Extraction and Parsing")
print("=" * 60)

# Test SMS Extractor keyword matching
extractor = SMSExtractor()
print("\n1. Testing SMS Extractor Keywords:")
print(f"   Total keywords: {len(extractor.FINANCIAL_SENDERS)}")
print(f"   Sample keywords: {extractor.FINANCIAL_SENDERS[:5]}")

# Check if messages would be filtered
for i, msg in enumerate(test_messages, 1):
    matches = [kw for kw in extractor.FINANCIAL_SENDERS if kw.lower() in msg.lower()]
    print(f"\n   Message {i}: {matches[:3] if matches else 'NO MATCH'}")
    print(f"   Preview: {msg[:50]}...")

# Test Expense Parser
parser = ExpenseParser()
print("\n\n2. Testing Expense Parser:")
print(f"   Total patterns: {len(parser.PATTERNS)}")

for i, msg in enumerate(test_messages, 1):
    print(f"\n   Message {i}:")
    print(f"   Text: {msg[:80]}...")

    result = parser.parse_message(msg)
    if result:
        print(f"   ✓ PARSED: Amount={result.get('amount')}, Merchant={result.get('merchant')}")
    else:
        print(f"   ✗ FAILED TO PARSE")

print("\n\n3. Testing direct extraction from database:")
try:
    import os
    db_path = os.path.expanduser("~/Library/Messages/chat.db")
    if os.path.exists(db_path):
        print(f"   Database found at: {db_path}")

        # Try extracting without date filter first
        import pandas as pd
        df = extractor.extract_messages()
        print(f"   ✓ Extracted {len(df)} messages (no date filter)")

        if len(df) > 0:
            print(f"\n   Sample extracted messages:")
            for idx, row in df.head(3).iterrows():
                print(f"   - {row['date']}: {row['text'][:60]}...")
        else:
            print("   ⚠ No messages extracted - checking why...")

            # Debug: try raw query
            import sqlite3
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()

            # Check messages with SAR
            cursor.execute("SELECT COUNT(*) FROM message WHERE text LIKE '%SAR%'")
            sar_count = cursor.fetchone()[0]
            print(f"   Messages containing 'SAR': {sar_count}")

            # Check messages with شراء
            cursor.execute("SELECT COUNT(*) FROM message WHERE text LIKE '%شراء%'")
            arabic_count = cursor.fetchone()[0]
            print(f"   Messages containing 'شراء': {arabic_count}")

            conn.close()
    else:
        print(f"   ⚠ Database not found (expected on Linux)")
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
