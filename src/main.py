"""
Main - Main entry point and workflow orchestrator
"""
import argparse
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from sms_extractor import SMSExtractor
from expense_parser import ExpenseParser
from database import ExpenseDatabase
from categorizer import ExpenseCategorizer
from analyzer import ExpenseAnalyzer
from exporter import ExpenseExporter


class ExpenseWorkflow:
    """Orchestrate the complete expense tracking workflow"""

    def __init__(self, db_path: str = "data/expenses.db", use_ai: bool = True):
        """
        Initialize workflow

        Args:
            db_path: Path to SQLite database
            use_ai: Whether to use AI for categorization
        """
        load_dotenv()

        self.db = ExpenseDatabase(db_path)
        self.parser = ExpenseParser()
        self.categorizer = ExpenseCategorizer(use_ai=use_ai)
        self.analyzer = ExpenseAnalyzer(self.db)
        self.exporter = ExpenseExporter(self.db)

    def process_messages(
        self,
        start_date: str,
        end_date: str,
        messages_db_path: str = None
    ) -> dict:
        """
        Complete workflow: extract, parse, categorize, and store expenses

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            messages_db_path: Path to Messages database

        Returns:
            Dictionary with processing results
        """
        print("=" * 80)
        print(f"Processing expenses from {start_date} to {end_date}")
        print("=" * 80)

        # Step 1: Extract SMS messages
        print("\n[1/5] Extracting SMS messages...")
        extractor = SMSExtractor(db_path=messages_db_path)
        messages_df = extractor.extract_messages(start_date=start_date, end_date=end_date)

        print(f"  ✓ Found {len(messages_df)} potential expense messages")

        if messages_df.empty:
            print("\n⚠ No messages found. Exiting.")
            return {'status': 'no_messages', 'count': 0}

        # Step 2: Parse expenses from messages
        print("\n[2/5] Parsing expense data...")
        expenses_df = self.parser.parse_messages_batch(messages_df)

        parsing_stats = self.parser.get_parsing_stats(messages_df, expenses_df)
        print(f"  ✓ Parsed {len(expenses_df)} expenses ({parsing_stats['parsing_rate']*100:.1f}% success rate)")
        print(f"  ✓ Total amount: ${parsing_stats['total_amount']:,.2f}")

        if expenses_df.empty:
            print("\n⚠ No expenses could be parsed. Exiting.")
            return {'status': 'no_expenses', 'count': 0}

        # Step 3: Categorize expenses
        print("\n[3/5] Categorizing expenses...")

        # Get learned merchant categories from database
        merchant_map = {}
        for merchant in expenses_df['merchant'].unique():
            learned_category = self.db.get_merchant_category(merchant)
            if learned_category:
                merchant_map[merchant] = learned_category

        expenses_df = self.categorizer.categorize_batch(expenses_df, merchant_map)

        # Count by method
        method_counts = expenses_df['category_method'].value_counts().to_dict()
        print(f"  ✓ Categorized {len(expenses_df)} expenses")
        for method, count in method_counts.items():
            print(f"    - {method}: {count}")

        # Step 4: Save to database
        print("\n[4/5] Saving to database...")

        # Save merchant-category mappings for learning
        for _, row in expenses_df.iterrows():
            if row['category_confidence'] >= 0.8:
                self.db.save_merchant_category_mapping(
                    row['merchant'],
                    row['category'],
                    row['category_confidence']
                )

        # Save expenses
        count = self.db.add_expenses_batch(expenses_df)
        print(f"  ✓ Saved {count} expenses to database")

        # Step 5: Generate summary
        print("\n[5/5] Generating summary...")
        stats = self.db.get_statistics(start_date=start_date, end_date=end_date)

        print(f"\n📊 Summary:")
        print(f"  Total expenses: {stats['total_expenses']}")
        print(f"  Total amount: ${stats['total_amount']:,.2f}")
        print(f"  Average: ${stats['average_expense']:.2f}")

        if stats['by_category']:
            print(f"\n  Top categories:")
            for i, (cat, amount) in enumerate(list(stats['by_category'].items())[:5], 1):
                print(f"    {i}. {cat}: ${amount:,.2f}")

        print("\n" + "=" * 80)
        print("✓ Processing complete!")
        print("=" * 80)

        return {
            'status': 'success',
            'messages_found': len(messages_df),
            'expenses_parsed': len(expenses_df),
            'expenses_saved': count,
            'total_amount': stats['total_amount']
        }

    def run_monthly_review(self, year: int = None, month: int = None):
        """
        Run complete monthly review and export

        Args:
            year: Year (defaults to current)
            month: Month (defaults to current)
        """
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month

        print("=" * 80)
        print(f"Monthly Review for {year}-{month:02d}")
        print("=" * 80)

        # Generate and display report
        report = self.analyzer.generate_monthly_report(year, month)
        print(report)

        # Export in all formats
        print("\nExporting reports...")
        exports = self.exporter.export_all_formats(year, month)

        print("\n📁 Exported files:")
        for format_name, path in exports.items():
            if not path.startswith("Error"):
                print(f"  ✓ {format_name.upper()}: {path}")
            else:
                print(f"  ✗ {format_name.upper()}: {path}")

        print("\n" + "=" * 80)


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='Expense Tracker - Process SMS messages and track expenses',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process messages for current month
  python src/main.py process --this-month

  # Process messages for specific date range
  python src/main.py process --start-date 2025-01-01 --end-date 2025-01-31

  # Generate monthly review
  python src/main.py review --year 2025 --month 1

  # Process and review in one command
  python src/main.py process --this-month --review
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Process command
    process_parser = subparsers.add_parser('process', help='Process SMS messages')
    process_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    process_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    process_parser.add_argument('--this-month', action='store_true', help='Process current month')
    process_parser.add_argument('--last-month', action='store_true', help='Process last month')
    process_parser.add_argument('--messages-db', help='Path to Messages database')
    process_parser.add_argument('--no-ai', action='store_true', help='Disable AI categorization')
    process_parser.add_argument('--review', action='store_true', help='Generate review after processing')

    # Review command
    review_parser = subparsers.add_parser('review', help='Generate monthly review')
    review_parser.add_argument('--year', type=int, help='Year')
    review_parser.add_argument('--month', type=int, help='Month (1-12)')
    review_parser.add_argument('--this-month', action='store_true', help='Current month')
    review_parser.add_argument('--last-month', action='store_true', help='Last month')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export expenses')
    export_parser.add_argument('--year', type=int, help='Year')
    export_parser.add_argument('--month', type=int, help='Month (1-12)')
    export_parser.add_argument('--format', choices=['csv', 'excel', 'json', 'report', 'all'], default='all')
    export_parser.add_argument('--output', default='reports', help='Output directory')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize workflow
    use_ai = not getattr(args, 'no_ai', False)
    workflow = ExpenseWorkflow(use_ai=use_ai)

    # Process command
    if args.command == 'process':
        # Determine date range
        if args.this_month:
            now = datetime.now()
            start_date = f"{now.year}-{now.month:02d}-01"
            end_date = now.strftime("%Y-%m-%d")
        elif args.last_month:
            now = datetime.now()
            first_day = datetime(now.year, now.month, 1)
            last_month_end = first_day - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            start_date = last_month_start.strftime("%Y-%m-%d")
            end_date = last_month_end.strftime("%Y-%m-%d")
        elif args.start_date and args.end_date:
            start_date = args.start_date
            end_date = args.end_date
        else:
            print("Error: Must specify date range (--start-date/--end-date, --this-month, or --last-month)")
            return

        # Process messages
        result = workflow.process_messages(
            start_date=start_date,
            end_date=end_date,
            messages_db_path=args.messages_db
        )

        # Generate review if requested
        if args.review and result['status'] == 'success':
            if args.this_month:
                now = datetime.now()
                workflow.run_monthly_review(now.year, now.month)
            elif args.last_month:
                now = datetime.now()
                first_day = datetime(now.year, now.month, 1)
                last_month = first_day - timedelta(days=1)
                workflow.run_monthly_review(last_month.year, last_month.month)

    # Review command
    elif args.command == 'review':
        if args.this_month:
            now = datetime.now()
            year, month = now.year, now.month
        elif args.last_month:
            now = datetime.now()
            first_day = datetime(now.year, now.month, 1)
            last_month = first_day - timedelta(days=1)
            year, month = last_month.year, last_month.month
        elif args.year and args.month:
            year, month = args.year, args.month
        else:
            now = datetime.now()
            year, month = now.year, now.month

        workflow.run_monthly_review(year, month)

    # Export command
    elif args.command == 'export':
        year = args.year or datetime.now().year
        month = args.month or datetime.now().month

        if args.format == 'all':
            exports = workflow.exporter.export_all_formats(year, month, args.output)
            print(f"\nExported expenses for {year}-{month:02d}:")
            for format_name, path in exports.items():
                print(f"  {format_name}: {path}")
        else:
            # Single format export logic here
            print(f"Exporting {args.format} for {year}-{month:02d}...")


if __name__ == '__main__':
    main()
