#!/usr/bin/env python3
"""
Add currency column to existing expenses table
"""
import sqlite3
import os

db_path = 'data/expenses.db'

print("=" * 80)
print("Adding Currency Column to Database")
print("=" * 80)

if not os.path.exists(db_path):
    print("\n❌ Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if currency column already exists
cursor.execute("PRAGMA table_info(expenses)")
columns = [row[1] for row in cursor.fetchall()]

if 'currency' in columns:
    print("\n✓ Currency column already exists!")
else:
    print("\nAdding currency column...")
    try:
        cursor.execute("ALTER TABLE expenses ADD COLUMN currency TEXT DEFAULT 'SAR'")
        conn.commit()
        print("✓ Currency column added successfully!")
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        conn.close()
        exit(1)

# Set currency for existing records based on raw_message
print("\nUpdating currency for existing records...")
cursor.execute("SELECT id, raw_message FROM expenses WHERE currency IS NULL OR currency = ''")
records = cursor.fetchall()

updated = 0
for record_id, raw_message in records:
    currency = 'SAR'  # Default

    if raw_message:
        msg_upper = raw_message.upper()
        if 'SAR' in msg_upper or 'ريال' in raw_message or 'SR' in msg_upper:
            currency = 'SAR'
        elif '$' in raw_message or 'USD' in msg_upper:
            currency = 'USD'
        elif '€' in raw_message or 'EUR' in msg_upper:
            currency = 'EUR'
        elif '£' in raw_message or 'GBP' in msg_upper:
            currency = 'GBP'
        elif '₹' in raw_message or 'INR' in msg_upper or 'RS.' in msg_upper:
            currency = 'INR'

    cursor.execute("UPDATE expenses SET currency = ? WHERE id = ?", (currency, record_id))
    updated += 1

conn.commit()
print(f"✓ Updated {updated:,} records")

# Show currency breakdown
print("\n📊 Currency Breakdown:")
cursor.execute("""
    SELECT currency, COUNT(*), SUM(amount)
    FROM expenses
    GROUP BY currency
    ORDER BY COUNT(*) DESC
""")

for currency, count, total in cursor.fetchall():
    symbol = {'SAR': 'SAR', 'USD': '$', 'EUR': '€', 'GBP': '£', 'INR': '₹'}.get(currency, currency)
    print(f"  {currency}: {count:4,} expenses, {symbol}{total:12,.2f}")

conn.close()

print("\n" + "=" * 80)
print("✓ Database migration complete!")
print("=" * 80)
