"""
Analyzer - Data analysis and insights for expenses
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import ExpenseDatabase


class ExpenseAnalyzer:
    """Analyze expense data and generate insights"""

    def __init__(self, db: ExpenseDatabase):
        """
        Initialize analyzer

        Args:
            db: ExpenseDatabase instance
        """
        self.db = db

    def get_monthly_summary(self, year: int, month: int) -> Dict:
        """
        Get summary for a specific month

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)

        Returns:
            Dictionary with monthly summary
        """
        # Get date range for the month
        start_date = f"{year}-{month:02d}-01"

        # Calculate last day of month
        if month == 12:
            end_date = f"{year}-12-31"
        else:
            next_month = datetime(year, month + 1, 1)
            last_day = next_month - timedelta(days=1)
            end_date = last_day.strftime("%Y-%m-%d")

        # Get expenses
        df = self.db.get_expenses(start_date=start_date, end_date=end_date)

        if df.empty:
            return {
                'year': year,
                'month': month,
                'total_expenses': 0,
                'total_amount': 0,
                'average_per_day': 0,
                'transaction_count': 0,
                'by_category': {},
                'top_merchants': {},
                'daily_spending': {}
            }

        # Calculate statistics
        total_amount = float(df['amount'].sum())
        transaction_count = len(df)

        # Days in month
        days_in_month = (datetime(year, month + 1, 1) - timedelta(days=1)).day if month < 12 else 31

        # Group by category
        by_category = df.groupby('category')['amount'].sum().to_dict()

        # Top merchants
        top_merchants = df.groupby('merchant')['amount'].sum().nlargest(10).to_dict()

        # Daily spending
        df['date_only'] = pd.to_datetime(df['date']).dt.date
        daily_spending = df.groupby('date_only')['amount'].sum().to_dict()
        daily_spending = {str(k): float(v) for k, v in daily_spending.items()}

        return {
            'year': year,
            'month': month,
            'total_amount': total_amount,
            'average_per_day': total_amount / days_in_month,
            'transaction_count': transaction_count,
            'average_transaction': total_amount / transaction_count if transaction_count > 0 else 0,
            'by_category': {k: float(v) for k, v in by_category.items()},
            'top_merchants': {k: float(v) for k, v in top_merchants.items()},
            'daily_spending': daily_spending
        }

    def compare_months(self, year1: int, month1: int, year2: int, month2: int) -> Dict:
        """
        Compare spending between two months

        Args:
            year1, month1: First month
            year2, month2: Second month

        Returns:
            Comparison dictionary
        """
        summary1 = self.get_monthly_summary(year1, month1)
        summary2 = self.get_monthly_summary(year2, month2)

        # Calculate changes
        amount_change = summary2['total_amount'] - summary1['total_amount']
        amount_change_pct = (amount_change / summary1['total_amount'] * 100) if summary1['total_amount'] > 0 else 0

        transaction_change = summary2['transaction_count'] - summary1['transaction_count']

        return {
            'month1': f"{year1}-{month1:02d}",
            'month2': f"{year2}-{month2:02d}",
            'amount_change': amount_change,
            'amount_change_pct': amount_change_pct,
            'transaction_change': transaction_change,
            'summary1': summary1,
            'summary2': summary2
        }

    def get_category_trends(self, months: int = 6) -> pd.DataFrame:
        """
        Get spending trends by category over time

        Args:
            months: Number of months to analyze

        Returns:
            DataFrame with monthly category spending
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)

        df = self.db.get_expenses(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )

        if df.empty:
            return pd.DataFrame()

        # Create year-month column
        df['year_month'] = pd.to_datetime(df['date']).dt.to_period('M')

        # Pivot table: months as rows, categories as columns
        trends = df.pivot_table(
            values='amount',
            index='year_month',
            columns='category',
            aggfunc='sum',
            fill_value=0
        )

        return trends

    def detect_anomalies(self, threshold: float = 2.0) -> List[Dict]:
        """
        Detect unusual spending patterns

        Args:
            threshold: Number of standard deviations for anomaly detection

        Returns:
            List of anomalous transactions
        """
        # Get last 90 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        df = self.db.get_expenses(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )

        if df.empty or len(df) < 10:
            return []

        # Calculate statistics
        mean_amount = df['amount'].mean()
        std_amount = df['amount'].std()

        # Find anomalies (amounts more than threshold std devs from mean)
        anomalies = df[df['amount'] > mean_amount + (threshold * std_amount)]

        results = []
        for idx, row in anomalies.iterrows():
            results.append({
                'date': row['date'],
                'merchant': row['merchant'],
                'amount': float(row['amount']),
                'category': row['category'],
                'deviation': (row['amount'] - mean_amount) / std_amount if std_amount > 0 else 0
            })

        return results

    def get_spending_by_day_of_week(self, months: int = 3) -> Dict:
        """
        Analyze spending patterns by day of week

        Args:
            months: Number of months to analyze

        Returns:
            Dictionary with spending by day of week
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)

        df = self.db.get_expenses(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )

        if df.empty:
            return {}

        df['day_of_week'] = pd.to_datetime(df['date']).dt.day_name()

        result = df.groupby('day_of_week')['amount'].agg(['sum', 'mean', 'count']).to_dict()

        return {
            'total': result['sum'],
            'average': result['mean'],
            'count': result['count']
        }

    def get_top_categories(self, limit: int = 5, months: int = 1) -> List[Dict]:
        """
        Get top spending categories

        Args:
            limit: Number of top categories to return
            months: Number of months to analyze

        Returns:
            List of top categories with spending data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)

        df = self.db.get_expenses(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )

        if df.empty:
            return []

        category_summary = df.groupby('category').agg({
            'amount': ['sum', 'count', 'mean']
        }).round(2)

        category_summary.columns = ['total', 'count', 'average']
        category_summary = category_summary.sort_values('total', ascending=False).head(limit)

        results = []
        total_spending = df['amount'].sum()

        for category, row in category_summary.iterrows():
            results.append({
                'category': category,
                'total_amount': float(row['total']),
                'transaction_count': int(row['count']),
                'average_amount': float(row['average']),
                'percentage': float(row['total'] / total_spending * 100) if total_spending > 0 else 0
            })

        return results

    def generate_monthly_report(self, year: int, month: int) -> str:
        """
        Generate a text report for the month

        Args:
            year: Year
            month: Month

        Returns:
            Formatted text report
        """
        summary = self.get_monthly_summary(year, month)

        # Get previous month for comparison
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1

        comparison = self.compare_months(prev_year, prev_month, year, month)

        report = f"""
╔════════════════════════════════════════════════════════════════╗
║           MONTHLY EXPENSE REPORT - {year}-{month:02d}                  ║
╚════════════════════════════════════════════════════════════════╝

OVERVIEW
────────────────────────────────────────────────────────────────
Total Spending:        ${summary['total_amount']:,.2f}
Total Transactions:    {summary['transaction_count']}
Average per Day:       ${summary['average_per_day']:,.2f}
Average Transaction:   ${summary['average_transaction']:,.2f}

MONTH-OVER-MONTH CHANGE
────────────────────────────────────────────────────────────────
Change:                ${comparison['amount_change']:+,.2f} ({comparison['amount_change_pct']:+.1f}%)
Transaction Change:    {comparison['transaction_change']:+d}

TOP CATEGORIES
────────────────────────────────────────────────────────────────
"""
        for i, cat in enumerate(self.get_top_categories(limit=5, months=1), 1):
            report += f"{i}. {cat['category']:<20} ${cat['total_amount']:>10,.2f} ({cat['percentage']:>5.1f}%)\n"

        report += f"""
TOP MERCHANTS
────────────────────────────────────────────────────────────────
"""
        for i, (merchant, amount) in enumerate(list(summary['top_merchants'].items())[:5], 1):
            report += f"{i}. {merchant:<30} ${amount:>10,.2f}\n"

        # Anomalies
        anomalies = self.detect_anomalies()
        if anomalies:
            report += f"""
UNUSUAL TRANSACTIONS
────────────────────────────────────────────────────────────────
"""
            for anomaly in anomalies[:5]:
                report += f"• {anomaly['merchant']:<20} ${anomaly['amount']:>10,.2f} on {anomaly['date']}\n"

        return report


def main():
    """Test analyzer"""
    db = ExpenseDatabase("data/expenses.db")
    analyzer = ExpenseAnalyzer(db)

    # Get current month
    now = datetime.now()

    # Generate report
    report = analyzer.generate_monthly_report(now.year, now.month)
    print(report)


if __name__ == '__main__':
    main()
