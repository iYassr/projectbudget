#!/usr/bin/env python3
"""
Show all unique message senders in your TXT export
Use this to identify which senders to add to config.py
"""
import os
import re
from datetime import datetime
from pathlib import Path
from collections import Counter

# Path to TXT export folder
EXPORT_PATH = os.path.expanduser("~/messages_export")

print("=" * 80)
print("Analyzing Message Senders")
print("=" * 80)

if not os.path.exists(EXPORT_PATH):
    print(f"\n❌ Export folder not found at: {EXPORT_PATH}")
    sys.exit(1)

print(f"\n📂 Scanning: {EXPORT_PATH}")

# Find all TXT files
txt_files = list(Path(EXPORT_PATH).rglob("*.txt"))
print(f"   Found {len(txt_files):,} conversation files\n")

senders = Counter()
total_messages = 0

# Financial keywords to identify potential bank messages
FINANCIAL_KEYWORDS = [
    'SAR', 'ريال', 'شراء', 'مبلغ', 'بطاقة', 'حوالة', 'رصيد',
    'purchase', 'amount', 'card', 'visa', 'transfer', 'balance'
]

for txt_file in txt_files:
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            file_lines = f.readlines()

        i = 0
        while i < len(file_lines):
            line = file_lines[i].strip()

            # Look for date line
            date_match = re.match(r'([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)', line)

            if date_match:
                # Next line should be sender
                i += 1
                if i >= len(file_lines):
                    break

                sender = file_lines[i].strip()

                # Skip messages sent by "Me"
                if sender == "Me":
                    i += 1
                    continue

                # Collect message lines to check for financial content
                i += 1
                message_lines = []

                while i < len(file_lines):
                    next_line = file_lines[i].strip()

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

                    # Check if message contains financial keywords
                    if any(kw.lower() in msg_text.lower() for kw in FINANCIAL_KEYWORDS):
                        senders[sender] += 1
                        total_messages += 1
            else:
                i += 1

    except Exception as e:
        continue

print(f"📊 Found {total_messages:,} financial messages from {len(senders)} unique senders:\n")
print("=" * 80)
print(f"{'SENDER':<40} {'COUNT':>10}")
print("=" * 80)

for sender, count in senders.most_common():
    print(f"{sender:<40} {count:>10,}")

print("=" * 80)

print("\n📋 To configure sender whitelist:")
print("   1. Edit config.py")
print("   2. Add senders you want to ALLOWED_SENDERS list")
print("   3. Use exact sender names from the list above")

print("\n💡 Recommended: Only add your bank and payment service senders")
print("   This will exclude personal contacts and reduce false positives\n")
