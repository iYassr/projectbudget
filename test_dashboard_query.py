#!/usr/bin/env python3
"""
Test what the dashboard query returns
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import ExpenseDatabase

print("=" * 80)
print("Testing Dashboard Database Query")
print("=" * 80)

db = ExpenseDatabase('data/expenses.db')

# This is the same query the dashboard uses
df = db.get_expenses(start_date='2022-01-01', end_date='2025-12-31')

print(f'\n📊 Query Results:')
print(f'  Total expenses: {len(df):,}')
print(f'  Total amount: ${df["amount"].sum():,.2f}')
print(f'  Date range: {df["date"].min()} to {df["date"].max()}')

# Check for Amazon
amazon = df[df['merchant'].str.contains('AMAZON', case=False, na=False)]
print(f'\n🛒 Amazon Transactions:')
print(f'  Count: {len(amazon)}')
if len(amazon) > 0:
    print(f'  Total: ${amazon["amount"].sum():,.2f}')
    print(f'  Merchants found: {amazon["merchant"].unique().tolist()}')
    print(f'\n  Sample transactions:')
    for idx, row in amazon.head(5).iterrows():
        print(f'    {row["date"]} | {row["merchant"]:20} | ${row["amount"]:8.2f}')
else:
    print('  ❌ No Amazon transactions found!')

# Top 10 merchants
print(f'\n🏪 Top 10 Merchants (what dashboard should show):')
top_merchants = df.groupby('merchant')['amount'].sum().sort_values(ascending=False).head(10)
for merchant, amount in top_merchants.items():
    print(f'  {merchant:30} ${amount:12,.2f}')

# Check if dataframe is empty or has issues
print(f'\n🔍 Data Quality Check:')
print(f'  Empty dataframe: {df.empty}')
print(f'  Columns: {df.columns.tolist()}')
print(f'  Data types: {df.dtypes.to_dict()}')

print("\n" + "=" * 80)
print("If this shows Amazon but dashboard doesn't, try:")
print("  1. Stop the dashboard (Ctrl+C)")
print("  2. Clear Streamlit cache: rm -rf ~/.streamlit/cache")
print("  3. Restart: streamlit run src/dashboard.py")
print("=" * 80)
