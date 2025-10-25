#!/usr/bin/env python3
"""
Check what's in the expense database
"""
import sqlite3
import pandas as pd
from datetime import datetime

db_path = 'data/expenses.db'

print("=" * 80)
print("Database Analysis")
print("=" * 80)

conn = sqlite3.connect(db_path)

# Total expenses
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM expenses")
total = cursor.fetchone()[0]
print(f"\nTotal expenses in database: {total:,}")

# Date range
cursor.execute("SELECT MIN(date), MAX(date) FROM expenses")
min_date, max_date = cursor.fetchone()
print(f"Date range: {min_date} to {max_date}")

# Total amount
cursor.execute("SELECT SUM(amount) FROM expenses")
total_amount = cursor.fetchone()[0]
print(f"Total amount: ${total_amount:,.2f}")

# By year
print("\n--- Expenses by Year ---")
df = pd.read_sql_query("SELECT * FROM expenses", conn)
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year

yearly = df.groupby('year').agg({
    'amount': ['sum', 'count']
}).round(2)
yearly.columns = ['Total Amount', 'Count']
print(yearly.to_string())

# By merchant (top 20)
print("\n--- Top 20 Merchants ---")
merchants = df.groupby('merchant').agg({
    'amount': ['sum', 'count'],
    'date': ['min', 'max']
}).round(2)
merchants.columns = ['Total', 'Count', 'First Date', 'Last Date']
merchants = merchants.sort_values('Total', ascending=False).head(20)
print(merchants.to_string())

# Check for duplicates
print("\n--- Duplicate Check ---")
cursor.execute("""
    SELECT date, merchant, amount, COUNT(*) as cnt
    FROM expenses
    GROUP BY date, merchant, amount
    HAVING COUNT(*) > 1
    LIMIT 10
""")
duplicates = cursor.fetchall()
if duplicates:
    print(f"Found {len(duplicates)} potential duplicate groups:")
    for dup in duplicates[:5]:
        print(f"  {dup[0]} | {dup[1]} | ${dup[2]} | {dup[3]} times")
else:
    print("No obvious duplicates found")

# Recent expenses
print("\n--- Most Recent 10 Expenses ---")
cursor.execute("""
    SELECT date, merchant, amount, category
    FROM expenses
    ORDER BY date DESC
    LIMIT 10
""")
recent = cursor.fetchall()
for r in recent:
    print(f"  {r[0]} | {r[1][:30]:30} | ${r[2]:8.2f} | {r[3]}")

conn.close()

print("\n" + "=" * 80)
