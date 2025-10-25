"""
Exporter - Export expense data to various formats
"""
import pandas as pd
import os
from datetime import datetime
from typing import Optional
from database import ExpenseDatabase
from analyzer import ExpenseAnalyzer
import json


class ExpenseExporter:
    """Export expense data to multiple formats"""

    def __init__(self, db: ExpenseDatabase):
        """
        Initialize exporter

        Args:
            db: ExpenseDatabase instance
        """
        self.db = db
        self.analyzer = ExpenseAnalyzer(db)

    def export_to_csv(
        self,
        output_path: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Export expenses to CSV

        Args:
            output_path: Output file path
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Path to exported file
        """
        df = self.db.get_expenses(start_date=start_date, end_date=end_date)

        if df.empty:
            raise ValueError("No expenses to export")

        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Export
        df.to_csv(output_path, index=False)

        return output_path

    def export_to_excel(
        self,
        output_path: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_summary: bool = True
    ) -> str:
        """
        Export expenses to Excel with multiple sheets

        Args:
            output_path: Output file path
            start_date: Start date filter
            end_date: End date filter
            include_summary: Whether to include summary sheets

        Returns:
            Path to exported file
        """
        df = self.db.get_expenses(start_date=start_date, end_date=end_date)

        if df.empty:
            raise ValueError("No expenses to export")

        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Main expenses sheet
            df.to_excel(writer, sheet_name='Expenses', index=False)

            if include_summary:
                # Category summary
                if 'category' in df.columns:
                    category_summary = df.groupby('category').agg({
                        'amount': ['sum', 'count', 'mean']
                    }).round(2)
                    category_summary.columns = ['Total', 'Count', 'Average']
                    category_summary = category_summary.sort_values('Total', ascending=False)
                    category_summary.to_excel(writer, sheet_name='By Category')

                # Merchant summary
                merchant_summary = df.groupby('merchant').agg({
                    'amount': ['sum', 'count']
                }).round(2)
                merchant_summary.columns = ['Total', 'Count']
                merchant_summary = merchant_summary.sort_values('Total', ascending=False)
                merchant_summary.to_excel(writer, sheet_name='By Merchant')

                # Daily summary
                df['date_only'] = pd.to_datetime(df['date']).dt.date
                daily_summary = df.groupby('date_only')['amount'].sum().reset_index()
                daily_summary.columns = ['Date', 'Total']
                daily_summary.to_excel(writer, sheet_name='Daily', index=False)

        return output_path

    def export_monthly_report(
        self,
        year: int,
        month: int,
        output_path: str
    ) -> str:
        """
        Export a formatted monthly report

        Args:
            year: Year
            month: Month (1-12)
            output_path: Output file path

        Returns:
            Path to exported file
        """
        report = self.analyzer.generate_monthly_report(year, month)

        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(report)

        return output_path

    def export_to_google_sheets(
        self,
        spreadsheet_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Export expenses to Google Sheets

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            start_date: Start date filter
            end_date: End date filter

        Returns:
            URL to the Google Sheet

        Note: Requires Google Sheets API credentials to be configured
        """
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
        except ImportError:
            raise ImportError("Google Sheets export requires 'gspread' and 'oauth2client' packages")

        df = self.db.get_expenses(start_date=start_date, end_date=end_date)

        if df.empty:
            raise ValueError("No expenses to export")

        # Set up credentials
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if not creds_path:
            raise ValueError("GOOGLE_SHEETS_CREDENTIALS environment variable not set")

        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)

        # Open spreadsheet
        sheet = client.open_by_key(spreadsheet_id)

        # Update or create worksheet
        try:
            worksheet = sheet.worksheet("Expenses")
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title="Expenses", rows=1000, cols=20)

        # Convert DataFrame to list of lists
        data = [df.columns.tolist()] + df.astype(str).values.tolist()

        # Update sheet
        worksheet.update('A1', data)

        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

    def export_summary_json(
        self,
        output_path: str,
        year: int,
        month: int
    ) -> str:
        """
        Export monthly summary as JSON

        Args:
            output_path: Output file path
            year: Year
            month: Month

        Returns:
            Path to exported file
        """
        summary = self.analyzer.get_monthly_summary(year, month)

        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        return output_path

    def export_all_formats(
        self,
        year: int,
        month: int,
        output_dir: str = "reports"
    ) -> dict:
        """
        Export in all available formats

        Args:
            year: Year
            month: Month
            output_dir: Output directory

        Returns:
            Dictionary with paths to all exported files
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Date range for the month
        start_date = f"{year}-{month:02d}-01"

        # Calculate last day of month
        if month == 12:
            end_date = f"{year}-12-31"
        else:
            from datetime import datetime, timedelta
            next_month = datetime(year, month + 1, 1)
            last_day = next_month - timedelta(days=1)
            end_date = last_day.strftime("%Y-%m-%d")

        # Export to different formats
        base_filename = f"expenses_{year}_{month:02d}"

        exports = {}

        # CSV
        try:
            csv_path = os.path.join(output_dir, f"{base_filename}.csv")
            self.export_to_csv(csv_path, start_date, end_date)
            exports['csv'] = csv_path
        except Exception as e:
            exports['csv'] = f"Error: {e}"

        # Excel
        try:
            excel_path = os.path.join(output_dir, f"{base_filename}.xlsx")
            self.export_to_excel(excel_path, start_date, end_date)
            exports['excel'] = excel_path
        except Exception as e:
            exports['excel'] = f"Error: {e}"

        # Text report
        try:
            report_path = os.path.join(output_dir, f"{base_filename}_report.txt")
            self.export_monthly_report(year, month, report_path)
            exports['report'] = report_path
        except Exception as e:
            exports['report'] = f"Error: {e}"

        # JSON summary
        try:
            json_path = os.path.join(output_dir, f"{base_filename}_summary.json")
            self.export_summary_json(json_path, year, month)
            exports['json'] = json_path
        except Exception as e:
            exports['json'] = f"Error: {e}"

        return exports


def main():
    """Test exporter"""
    import argparse

    parser = argparse.ArgumentParser(description='Export expense data')
    parser.add_argument('--format', choices=['csv', 'excel', 'report', 'json', 'all'], default='all')
    parser.add_argument('--year', type=int, default=datetime.now().year)
    parser.add_argument('--month', type=int, default=datetime.now().month)
    parser.add_argument('--output', default='reports')

    args = parser.parse_args()

    db = ExpenseDatabase("data/expenses.db")
    exporter = ExpenseExporter(db)

    if args.format == 'all':
        exports = exporter.export_all_formats(args.year, args.month, args.output)
        print(f"\nExported expenses for {args.year}-{args.month:02d}:")
        for format_name, path in exports.items():
            print(f"  {format_name}: {path}")
    else:
        # Export single format
        base_filename = f"expenses_{args.year}_{args.month:02d}"
        start_date = f"{args.year}-{args.month:02d}-01"

        if args.format == 'csv':
            path = exporter.export_to_csv(
                os.path.join(args.output, f"{base_filename}.csv"),
                start_date=start_date
            )
        elif args.format == 'excel':
            path = exporter.export_to_excel(
                os.path.join(args.output, f"{base_filename}.xlsx"),
                start_date=start_date
            )
        elif args.format == 'report':
            path = exporter.export_monthly_report(
                args.year,
                args.month,
                os.path.join(args.output, f"{base_filename}_report.txt")
            )
        elif args.format == 'json':
            path = exporter.export_summary_json(
                os.path.join(args.output, f"{base_filename}_summary.json"),
                args.year,
                args.month
            )

        print(f"\nExported to: {path}")


if __name__ == '__main__':
    main()
