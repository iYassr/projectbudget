#!/usr/bin/env python3
"""
Recategorize merchants currently in "Other" category
Uses enhanced rule-based keywords to automatically recategorize
"""
import sqlite3
import sys
from src.categorizer import ExpenseCategorizer

def recategorize_others(use_ai=False, dry_run=True):
    """
    Recategorize all expenses in 'Other' category

    Args:
        use_ai: Whether to use AI for unknown merchants
        dry_run: If True, only show what would be changed without saving
    """
    # Connect to database
    conn = sqlite3.connect('data/expenses.db')
    cursor = conn.cursor()

    # Get all expenses in "Other" category
    cursor.execute("""
        SELECT id, merchant, amount, raw_message, category
        FROM expenses
        WHERE category = 'Other'
        ORDER BY merchant
    """)

    others = cursor.fetchall()

    if not others:
        print("✓ No expenses found in 'Other' category!")
        conn.close()
        return

    print(f"Found {len(others):,} expenses in 'Other' category")
    print("=" * 80)

    # Initialize categorizer
    categorizer = ExpenseCategorizer(use_ai=use_ai)

    # Track changes
    changes = {}
    unchanged = []

    for expense_id, merchant, amount, raw_message, old_category in others:
        # Try to categorize using rules (or AI if enabled)
        result = categorizer.categorize_expense(merchant, amount, raw_message, None)
        new_category = result['category']
        method = result['method']

        if new_category != 'Other':
            if new_category not in changes:
                changes[new_category] = []
            changes[new_category].append({
                'id': expense_id,
                'merchant': merchant,
                'method': method
            })
        else:
            unchanged.append(merchant)

    # Show results
    if changes:
        print(f"\n✓ Found {sum(len(v) for v in changes.values())} expenses that can be recategorized:\n")

        for category, expenses in sorted(changes.items()):
            print(f"\n{category} ({len(expenses)} expenses):")
            print("-" * 80)

            # Group by merchant
            merchants = {}
            for exp in expenses:
                merchant = exp['merchant']
                if merchant not in merchants:
                    merchants[merchant] = {'count': 0, 'method': exp['method']}
                merchants[merchant]['count'] += 1

            for merchant, info in sorted(merchants.items(), key=lambda x: x[1]['count'], reverse=True):
                method_icon = "🤖" if info['method'] == 'ai' else "📋"
                print(f"  {method_icon} {merchant:<50} ({info['count']} txns)")

    if unchanged:
        print(f"\n⚠️  {len(set(unchanged))} unique merchants remain in 'Other':")
        print("-" * 80)
        # Count occurrences
        merchant_counts = {}
        for merchant in unchanged:
            merchant_counts[merchant] = merchant_counts.get(merchant, 0) + 1

        for merchant, count in sorted(merchant_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"  • {merchant:<50} ({count} txns)")

        if len(merchant_counts) > 20:
            print(f"  ... and {len(merchant_counts) - 20} more")

    print("\n" + "=" * 80)

    # Apply changes if not dry run
    if not dry_run and changes:
        print("\nApplying changes to database...")

        for category, expenses in changes.items():
            expense_ids = [exp['id'] for exp in expenses]
            placeholders = ','.join('?' * len(expense_ids))
            cursor.execute(f"""
                UPDATE expenses
                SET category = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
            """, [category] + expense_ids)

        conn.commit()
        print(f"✓ Updated {sum(len(v) for v in changes.values())} expenses!")

        # Also update merchant cache
        print("✓ Merchant cache updated automatically")

    elif dry_run:
        print("\n💡 This was a DRY RUN - no changes were made")
        print("   Run with --apply to actually update the database")

    conn.close()

    # Show AI cost if applicable
    if use_ai:
        ai_count = sum(1 for cat_list in changes.values()
                      for exp in cat_list if exp['method'] == 'ai')
        if ai_count > 0:
            cost = ai_count * 0.0001
            print(f"\n💰 AI usage: {ai_count} calls (estimated cost: ${cost:.4f})")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Recategorize 'Other' merchants")
    parser.add_argument('--apply', action='store_true',
                       help='Actually apply changes (default is dry-run)')
    parser.add_argument('--use-ai', action='store_true',
                       help='Use AI for merchants that rules cannot categorize')

    args = parser.parse_args()

    dry_run = not args.apply

    if args.use_ai:
        print("🤖 AI categorization ENABLED")
    else:
        print("📋 Using rule-based categorization only")

    if dry_run:
        print("🔍 DRY RUN MODE - showing what would change\n")
    else:
        print("⚠️  APPLY MODE - will update database\n")

    recategorize_others(use_ai=args.use_ai, dry_run=dry_run)
