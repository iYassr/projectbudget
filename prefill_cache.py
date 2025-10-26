#!/usr/bin/env python3
"""
Pre-fill merchant cache with rule-based categorizations

This saves you money by caching common merchants before using AI.
Only unknown merchants will need AI categorization.
"""
import sys
import os
import json
import sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from categorizer import ExpenseCategorizer

print("=" * 80)
print("Pre-filling Merchant Cache with Rule-Based Categorizations")
print("=" * 80)

# Initialize categorizer (without AI)
categorizer = ExpenseCategorizer(use_ai=False)

# Get all unique merchants from database
db_path = 'data/expenses.db'
if not os.path.exists(db_path):
    print("\n❌ Database not found. Extract expenses first!")
    sys.exit(1)

print("\n[1/3] Loading merchants from database...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT merchant FROM expenses WHERE merchant IS NOT NULL")
merchants = [row[0] for row in cursor.fetchall()]
conn.close()

print(f"  Found {len(merchants):,} unique merchants")

# Categorize each merchant using rules
print("\n[2/3] Categorizing merchants with rules...")
categorized = 0
uncategorized = []

for merchant in merchants:
    merchant_key = merchant.upper().strip()

    # Skip if already in cache
    if merchant_key in categorizer.merchant_cache:
        continue

    # Try rule-based categorization
    category = categorizer._categorize_by_rules(merchant, None)

    if category:
        categorizer.merchant_cache[merchant_key] = category
        categorized += 1
    else:
        uncategorized.append(merchant)

print(f"  ✓ Categorized {categorized:,} merchants using rules")
print(f"  ⚠ {len(uncategorized):,} merchants need AI categorization")

# Save cache
print("\n[3/3] Saving merchant cache...")
categorizer._save_cache()
print(f"  ✓ Saved to {categorizer.cache_path}")

# Show summary
print("\n" + "=" * 80)
print("📊 Summary")
print("=" * 80)
print(f"Total merchants: {len(merchants):,}")
print(f"Cached (rules):  {categorized:,} (FREE)")
print(f"Need AI:         {len(uncategorized):,} (will cost ${len(uncategorized) * 0.0001:.4f} with OpenAI)")

if len(uncategorized) > 0 and len(uncategorized) <= 20:
    print(f"\n🔍 Merchants that need AI:")
    for merchant in uncategorized[:20]:
        print(f"  • {merchant}")

print("\n💡 Next steps:")
print("  1. The cache is now pre-filled with rule-based categories")
print("  2. When you enable AI, it will only categorize the uncategorized merchants")
print("  3. This saves you money by avoiding AI calls for common merchants!")
print("\n" + "=" * 80)
