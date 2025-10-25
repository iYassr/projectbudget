"""
Database - SQLite database operations for expense tracking
"""
import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import os


class ExpenseDatabase:
    """Manage expense data in SQLite database"""

    def __init__(self, db_path: str = "data/expenses.db"):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create expenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP NOT NULL,
                amount REAL NOT NULL,
                merchant TEXT NOT NULL,
                category TEXT,
                transaction_type TEXT DEFAULT 'expense',
                currency TEXT DEFAULT 'SAR',
                sender TEXT,
                raw_message TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index on date for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_date
            ON expenses(date)
        """)

        # Create index on category
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_category
            ON expenses(category)
        """)

        # Create categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                color TEXT,
                icon TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create merchant mappings table (for learning merchant -> category)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS merchant_categories (
                merchant TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def add_expense(self, expense: Dict) -> int:
        """
        Add a single expense to database

        Args:
            expense: Dictionary with expense data

        Returns:
            ID of inserted expense
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO expenses (date, amount, merchant, category, transaction_type, currency, sender, raw_message, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            expense['date'],
            expense['amount'],
            expense['merchant'],
            expense.get('category'),
            expense.get('transaction_type', 'expense'),
            expense.get('currency', 'SAR'),
            expense.get('sender'),
            expense.get('raw_message'),
            expense.get('notes', '')
        ))

        expense_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return expense_id

    def add_expenses_batch(self, expenses_df: pd.DataFrame) -> int:
        """
        Add multiple expenses from DataFrame

        Args:
            expenses_df: DataFrame with expense data

        Returns:
            Number of expenses added
        """
        conn = sqlite3.connect(self.db_path)

        # Ensure required columns exist
        required_cols = ['date', 'amount', 'merchant']
        if not all(col in expenses_df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")

        # Add default values for optional columns
        if 'category' not in expenses_df.columns:
            expenses_df['category'] = None
        if 'transaction_type' not in expenses_df.columns:
            expenses_df['transaction_type'] = 'expense'
        if 'sender' not in expenses_df.columns:
            expenses_df['sender'] = None
        if 'raw_message' not in expenses_df.columns:
            expenses_df['raw_message'] = None
        if 'notes' not in expenses_df.columns:
            expenses_df['notes'] = ''

        # Insert to database
        expenses_df.to_sql('expenses', conn, if_exists='append', index=False)

        count = len(expenses_df)
        conn.close()

        return count

    def get_expenses(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        merchant: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Query expenses from database

        Args:
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            category: Category filter
            merchant: Merchant filter

        Returns:
            DataFrame with expense data
        """
        conn = sqlite3.connect(self.db_path)

        query = "SELECT * FROM expenses WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        if category:
            query += " AND category = ?"
            params.append(category)

        if merchant:
            query += " AND merchant LIKE ?"
            params.append(f"%{merchant}%")

        query += " ORDER BY date DESC"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])

        return df

    def update_expense(self, expense_id: int, updates: Dict):
        """
        Update an expense

        Args:
            expense_id: ID of expense to update
            updates: Dictionary of fields to update
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build update query
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(expense_id)

        cursor.execute(f"""
            UPDATE expenses
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)

        conn.commit()
        conn.close()

    def update_category_batch(self, merchant: str, category: str):
        """
        Update category for all expenses from a specific merchant

        Args:
            merchant: Merchant name
            category: New category
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE expenses
            SET category = ?, updated_at = CURRENT_TIMESTAMP
            WHERE merchant = ?
        """, (category, merchant))

        conn.commit()
        conn.close()

    def delete_expense(self, expense_id: int):
        """Delete an expense"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))

        conn.commit()
        conn.close()

    def get_statistics(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """
        Get summary statistics

        Args:
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Dictionary with statistics
        """
        df = self.get_expenses(start_date=start_date, end_date=end_date)

        if df.empty:
            return {
                'total_expenses': 0,
                'total_amount': 0,
                'average_expense': 0,
                'expense_count': 0,
                'by_category': {},
                'top_merchants': {}
            }

        return {
            'total_expenses': len(df),
            'total_amount': float(df['amount'].sum()),
            'average_expense': float(df['amount'].mean()),
            'expense_count': len(df),
            'by_category': df.groupby('category')['amount'].sum().to_dict() if 'category' in df.columns else {},
            'top_merchants': df.groupby('merchant')['amount'].sum().nlargest(10).to_dict()
        }

    def save_merchant_category_mapping(self, merchant: str, category: str, confidence: float = 1.0):
        """
        Save a merchant -> category mapping for future auto-categorization

        Args:
            merchant: Merchant name
            category: Category
            confidence: Confidence score (0-1)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO merchant_categories (merchant, category, confidence, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (merchant, category, confidence))

        conn.commit()
        conn.close()

    def get_merchant_category(self, merchant: str) -> Optional[str]:
        """
        Get learned category for a merchant

        Args:
            merchant: Merchant name

        Returns:
            Category name or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT category FROM merchant_categories WHERE merchant = ?
        """, (merchant,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None


def main():
    """Test database operations"""
    db = ExpenseDatabase("data/test_expenses.db")

    # Test adding expense
    expense = {
        'date': datetime.now(),
        'amount': 25.50,
        'merchant': 'Starbucks',
        'category': 'Food & Dining',
        'sender': 'BankSMS',
        'raw_message': 'You spent $25.50 at Starbucks'
    }

    expense_id = db.add_expense(expense)
    print(f"Added expense with ID: {expense_id}")

    # Test querying
    expenses = db.get_expenses()
    print(f"\nTotal expenses in database: {len(expenses)}")
    print(expenses)

    # Test statistics
    stats = db.get_statistics()
    print(f"\nStatistics:")
    print(f"  Total amount: ${stats['total_amount']:.2f}")
    print(f"  Average: ${stats['average_expense']:.2f}")
    print(f"  Count: {stats['expense_count']}")


if __name__ == '__main__':
    main()
