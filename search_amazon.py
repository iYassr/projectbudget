#!/usr/bin/env python3
"""
Search for Amazon transactions in the database
"""
import sqlite3
import pandas as pd

db_path = 'data/expenses.db'

print("=" * 80)
print("Searching for Amazon Transactions")
print("=" * 80)

conn = sqlite3.connect(db_path)

# Search for any merchant containing "amazon" (case insensitive)
query = """
SELECT date, merchant, amount, category, sender
FROM expenses
WHERE LOWER(merchant) LIKE '%amazon%'
ORDER BY date DESC
"""

df = pd.read_sql_query(query, conn)

if df.empty:
    print("\n❌ No Amazon transactions found in database!")
    print("\nLet's check what merchants exist that might be Amazon:")

    # Get all unique merchants
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT merchant FROM expenses ORDER BY merchant")
    all_merchants = [row[0] for row in cursor.fetchall()]

    print(f"\nTotal unique merchants: {len(all_merchants)}")
    print("\nMerchants containing 'A' (first 20):")
    a_merchants = [m for m in all_merchants if m.upper().startswith('A')]
    for m in a_merchants[:20]:
        print(f"  - {m}")

    print("\nMerchants containing 'SA' (first 20):")
    sa_merchants = [m for m in all_merchants if 'SA' in m.upper()]
    for m in sa_merchants[:20]:
        print(f"  - {m}")

else:
    print(f"\n✓ Found {len(df)} Amazon transactions!")
    print(f"  Total amount: ${df['amount'].sum():,.2f}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")

    # Group by year
    df['year'] = pd.to_datetime(df['date']).dt.year
    yearly = df.groupby('year').agg({
        'amount': ['sum', 'count']
    })
    yearly.columns = ['Total', 'Count']

    print("\n--- Amazon Purchases by Year ---")
    print(yearly.to_string())

    print("\n--- All Amazon Transactions ---")
    for idx, row in df.iterrows():
        print(f"  {row['date']} | {row['merchant']:30} | ${row['amount']:8.2f}")

conn.close()

print("\n" + "=" * 80)
