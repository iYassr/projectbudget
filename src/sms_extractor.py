"""
SMS Extractor - Extract expense-related SMS messages from iPhone Messages database
"""
import sqlite3
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import argparse


class SMSExtractor:
    """Extract SMS messages from iPhone Messages database on Mac"""

    # Common bank and payment service identifiers (English & Arabic)
    FINANCIAL_SENDERS = [
        # English keywords
        'bank', 'card', 'credit', 'debit', 'payment', 'transaction',
        'paypal', 'venmo', 'zelle', 'cashapp', 'apple pay',
        'visa', 'mastercard', 'amex', 'discover',
        'chase', 'bofa', 'wells fargo', 'citi', 'capital one',
        'spent', 'purchased', 'paid', 'withdrawn', 'debited',
        'purchase', 'amount', 'balance', 'account',
        # Arabic keywords (Saudi banks)
        'شراء',      # Purchase
        'مبلغ',      # Amount
        'بطاقة',     # Card
        'حوالة',     # Transfer
        'رصيد',      # Balance
        'سحب',       # Withdrawal
        'ايداع',     # Deposit
        'مدى',       # Mada (Saudi debit card)
        'فيزا',      # Visa
        'ماستر',     # Master
        'ابل باي',   # Apple Pay
        'SAR',       # Saudi Riyal
        'ريال',      # Riyal
        'SR',        # Saudi Riyal abbreviation
        # Common Saudi bank abbreviations
        'SAIB',      # Saudi Investment Bank
        'RJHI',      # Al Rajhi Bank
        'NCB',       # National Commercial Bank
        'SABB',      # SABB Bank
        'SNB',       # Saudi National Bank
    ]

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SMS extractor

        Args:
            db_path: Path to Messages database. If None, uses default Mac location
        """
        if db_path is None:
            db_path = os.path.expanduser("~/Library/Messages/chat.db")

        self.db_path = db_path

        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Messages database not found at {self.db_path}.\n"
                "Make sure you're running this on a Mac with Messages synced from iPhone.\n"
                "You may need to grant Full Disk Access to Terminal:\n"
                "System Preferences → Security & Privacy → Privacy → Full Disk Access"
            )

    def extract_messages(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sender_filter: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Extract SMS messages from the database

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            sender_filter: List of sender IDs/numbers to filter by

        Returns:
            DataFrame with message data
        """
        # Connect to Messages database (read-only to be safe)
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

        try:
            # Build the query
            # The Messages database schema:
            # - message table: contains message text and metadata
            # - handle table: contains sender information (phone number, email)
            # - chat_message_join: links messages to chats

            query = """
            SELECT
                datetime(message.date/1000000000 + strftime('%s', '2001-01-01'), 'unixepoch', 'localtime') as date,
                message.text,
                handle.id as sender,
                message.is_from_me,
                message.service
            FROM message
            LEFT JOIN handle ON message.handle_id = handle.ROWID
            WHERE message.text IS NOT NULL
            """

            params = []

            # Add date filters
            if start_date:
                start_timestamp = self._date_to_cocoa_timestamp(start_date)
                query += " AND message.date >= ?"
                params.append(start_timestamp)

            if end_date:
                end_timestamp = self._date_to_cocoa_timestamp(end_date)
                query += " AND message.date <= ?"
                params.append(end_timestamp)

            # Only get received messages (not sent by user)
            query += " AND message.is_from_me = 0"

            query += " ORDER BY message.date DESC"

            # Execute query
            df = pd.read_sql_query(query, conn, params=params)

            # Filter for financial messages
            df = self._filter_financial_messages(df)

            return df

        finally:
            conn.close()

    def _date_to_cocoa_timestamp(self, date_str: str) -> int:
        """
        Convert date string to Cocoa timestamp (nanoseconds since 2001-01-01)

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Cocoa timestamp in nanoseconds
        """
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        cocoa_epoch = datetime(2001, 1, 1)
        seconds = (dt - cocoa_epoch).total_seconds()
        return int(seconds * 1000000000)

    def _filter_financial_messages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter messages to only include likely financial/expense messages

        Args:
            df: DataFrame of all messages

        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df

        # Create a mask for messages that contain financial keywords
        mask = df['text'].str.lower().apply(
            lambda text: any(keyword in str(text).lower() for keyword in self.FINANCIAL_SENDERS)
        )

        return df[mask].copy()

    def save_to_csv(self, df: pd.DataFrame, output_path: str):
        """Save extracted messages to CSV"""
        df.to_csv(output_path, index=False)
        print(f"Saved {len(df)} messages to {output_path}")

    def get_statistics(self, df: pd.DataFrame) -> Dict:
        """Get statistics about extracted messages"""
        return {
            'total_messages': len(df),
            'date_range': {
                'start': df['date'].min() if not df.empty else None,
                'end': df['date'].max() if not df.empty else None
            },
            'unique_senders': df['sender'].nunique() if not df.empty else 0,
            'top_senders': df['sender'].value_counts().head(5).to_dict() if not df.empty else {}
        }


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(description='Extract expense SMS messages from iPhone')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--db-path', help='Path to Messages database')
    parser.add_argument('--output', default='data/raw_messages.csv', help='Output CSV file')

    args = parser.parse_args()

    # Create extractor
    extractor = SMSExtractor(db_path=args.db_path)

    # Extract messages
    print(f"Extracting messages from {extractor.db_path}...")
    df = extractor.extract_messages(
        start_date=args.start_date,
        end_date=args.end_date
    )

    # Show statistics
    stats = extractor.get_statistics(df)
    print(f"\nExtraction Statistics:")
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Date range: {stats['date_range']['start']} to {stats['date_range']['end']}")
    print(f"  Unique senders: {stats['unique_senders']}")
    print(f"\nTop senders:")
    for sender, count in stats['top_senders'].items():
        print(f"  {sender}: {count} messages")

    # Save to CSV
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    extractor.save_to_csv(df, args.output)

    print(f"\nSample messages:")
    print(df[['date', 'sender', 'text']].head(10).to_string())


if __name__ == '__main__':
    main()
