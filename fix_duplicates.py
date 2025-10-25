#!/usr/bin/env python3
"""
Remove duplicate expenses from database
"""
import sqlite3
from datetime import datetime

db_path = 'data/expenses.db'

print("=" * 80)
print("Removing Duplicate Expenses")
print("=" * 80)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Count before
cursor.execute("SELECT COUNT(*) FROM expenses")
before_count = cursor.fetchone()[0]
print(f"\nExpenses before cleanup: {before_count:,}")

# Find duplicates (same date, merchant, amount)
cursor.execute("""
    SELECT date, merchant, amount, category, sender, raw_message
    FROM expenses
    GROUP BY date, merchant, amount
    HAVING COUNT(*) > 1
""")
duplicates = cursor.fetchall()
print(f"Duplicate groups found: {len(duplicates):,}")

if duplicates:
    print("\nRemoving duplicates...")

    # For each duplicate group, keep only one and delete the rest
    for date, merchant, amount, category, sender, raw_message in duplicates:
        # Get all IDs for this duplicate group
        cursor.execute("""
            SELECT id FROM expenses
            WHERE date = ? AND merchant = ? AND amount = ?
            ORDER BY id
        """, (date, merchant, amount))

        ids = [row[0] for row in cursor.fetchall()]

        # Keep the first one, delete the rest
        if len(ids) > 1:
            ids_to_delete = ids[1:]  # All except first
            placeholders = ','.join('?' * len(ids_to_delete))
            cursor.execute(f"DELETE FROM expenses WHERE id IN ({placeholders})", ids_to_delete)

    conn.commit()

    # Count after
    cursor.execute("SELECT COUNT(*) FROM expenses")
    after_count = cursor.fetchone()[0]

    removed = before_count - after_count
    print(f"\n✓ Removed {removed:,} duplicate expenses")
    print(f"✓ Remaining expenses: {after_count:,}")

    # Show summary after cleanup
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_amount = cursor.fetchone()[0]
    print(f"✓ Total amount: ${total_amount:,.2f}")

    # By year
    print("\n--- Expenses by Year (after cleanup) ---")
    cursor.execute("""
        SELECT
            strftime('%Y', date) as year,
            COUNT(*) as count,
            SUM(amount) as total
        FROM expenses
        GROUP BY year
        ORDER BY year
    """)

    for year, count, total in cursor.fetchall():
        print(f"  {year}: {count:4,} expenses, ${total:12,.2f}")

else:
    print("\n✓ No duplicates found!")

conn.close()

print("\n" + "=" * 80)
print("✓ Database cleanup complete!")
print("Restart your dashboard to see the updated data:")
print("  streamlit run src/dashboard.py")
print("=" * 80)
