"""
Expense Parser - Parse expense data from SMS messages
"""
import re
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import json


class ExpenseParser:
    """Parse expense information from SMS messages"""

    # Common currency symbols
    CURRENCY_SYMBOLS = ['$', '₹', '€', '£', '¥']

    # Regex patterns for different message formats
    PATTERNS = [
        # Arabic Pattern: "شراء بطاقة:9206 مبلغ:SAR 114.38 لدى:SASCO"
        {
            'pattern': r'شراء.*?مبلغ:?\s*(?:SAR|SR|ريال)?\s*([\d,]+\.?\d*)\s*(?:لدى|لدي):?\s*(.+?)(?:\s+في|\n|$)',
            'amount_group': 1,
            'merchant_group': 2
        },
        # Arabic Pattern: "حوالة ... مبلغ:SAR 10000 الى:Name"
        {
            'pattern': r'حوالة.*?(?:مبلغ|المبلغ):?\s*(?:SAR|SR|ريال)?\s*([\d,]+\.?\d*)',
            'amount_group': 1,
            'merchant_group': None,
            'default_merchant': 'Transfer'
        },
        # English/Arabic Mixed: "Amount:139.40 SAR ... At:Keeta"
        {
            'pattern': r'(?:Amount|مبلغ):?\s*(?:SAR|SR|ريال)?\s*([\d,]+\.?\d*)\s*(?:SAR|SR|ريال)?.*?(?:At|لدى|لدي):?\s*(.+?)(?:\s+A/C|\n|$)',
            'amount_group': 1,
            'merchant_group': 2
        },
        # Pattern: "spent $50.00 at Starbucks"
        {
            'pattern': r'(?:spent|paid|debited|charged)\s*(?:rs\.?|inr|usd|sar|sr)?\s*[\$₹€£¥]?\s*([\d,]+\.?\d*)\s*(?:at|on|to|for)?\s*(.+?)(?:\s+on|\.|$)',
            'amount_group': 1,
            'merchant_group': 2
        },
        # Pattern: "Rs 150.00 debited from account for AMAZON"
        {
            'pattern': r'(?:rs\.?|inr|usd|sar|sr)?\s*[\$₹€£¥]?\s*([\d,]+\.?\d*)\s*(?:debited|withdrawn|paid|spent).*?(?:for|at|to)\s*(.+?)(?:\s+on|\.|$)',
            'amount_group': 1,
            'merchant_group': 2
        },
        # Pattern: "Your card ending 1234 has been used for Rs 500 at McDonald's"
        {
            'pattern': r'card.*?(?:used|charged|debited).*?(?:for|of)\s*(?:rs\.?|inr|usd|sar|sr)?\s*[\$₹€£¥]?\s*([\d,]+\.?\d*)\s*(?:at|on|to|for)\s*(.+?)(?:\s+on|\.|$)',
            'amount_group': 1,
            'merchant_group': 2
        },
        # Pattern: "Transaction of $25.50 at Uber"
        {
            'pattern': r'transaction.*?(?:of|for)\s*(?:rs\.?|inr|usd|sar|sr)?\s*[\$₹€£¥]?\s*([\d,]+\.?\d*)\s*(?:at|on|to|for)?\s*(.+?)(?:\s+on|\.|$)',
            'amount_group': 1,
            'merchant_group': 2
        },
        # Pattern: "Purchase of Rs.1,200.00 at SWIGGY"
        {
            'pattern': r'purchase.*?(?:of|for)\s*(?:rs\.?|inr|usd|sar|sr)?\s*[\$₹€£¥]?\s*([\d,]+\.?\d*)\s*(?:at|on|to|for)?\s*(.+?)(?:\s+on|\.|$)',
            'amount_group': 1,
            'merchant_group': 2
        },
        # Pattern: "ATM withdrawal Rs 2000"
        {
            'pattern': r'(?:atm|cash).*?(?:withdrawal|withdrawn)\s*(?:of)?\s*(?:rs\.?|inr|usd|sar|sr)?\s*[\$₹€£¥]?\s*([\d,]+\.?\d*)',
            'amount_group': 1,
            'merchant_group': None,
            'default_merchant': 'ATM Withdrawal'
        },
        # Pattern: "Sent Rs 500 to John via PayTM"
        {
            'pattern': r'(?:sent|transferred)\s*(?:rs\.?|inr|usd|sar|sr)?\s*[\$₹€£¥]?\s*([\d,]+\.?\d*)\s*to\s*(.+?)\s*via',
            'amount_group': 1,
            'merchant_group': 2,
            'is_transfer': True
        }
    ]

    def __init__(self):
        """Initialize the expense parser"""
        pass

    def parse_message(self, message: str) -> Optional[Dict]:
        """
        Parse a single SMS message to extract expense information

        Args:
            message: SMS message text

        Returns:
            Dictionary with parsed expense data or None if no expense found
        """
        if not message or not isinstance(message, str):
            return None

        message = message.strip()

        # Try each pattern
        for pattern_info in self.PATTERNS:
            match = re.search(pattern_info['pattern'], message, re.IGNORECASE)

            if match:
                # Extract amount
                amount_str = match.group(pattern_info['amount_group'])
                amount = self._parse_amount(amount_str)

                if amount is None or amount <= 0:
                    continue

                # Extract merchant
                merchant = None
                if pattern_info['merchant_group'] is not None:
                    merchant = match.group(pattern_info['merchant_group'])
                    merchant = self._clean_merchant_name(merchant)

                if not merchant and 'default_merchant' in pattern_info:
                    merchant = pattern_info['default_merchant']

                # Determine transaction type
                trans_type = 'transfer' if pattern_info.get('is_transfer', False) else 'expense'

                return {
                    'amount': amount,
                    'merchant': merchant or 'Unknown',
                    'transaction_type': trans_type,
                    'raw_message': message,
                    'matched_pattern': pattern_info['pattern']
                }

        return None

    def parse_messages_batch(self, messages_df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse a batch of messages from a DataFrame

        Args:
            messages_df: DataFrame with columns: date, text, sender

        Returns:
            DataFrame with parsed expense data
        """
        expenses = []

        for idx, row in messages_df.iterrows():
            parsed = self.parse_message(row['text'])

            if parsed:
                expense = {
                    'date': row['date'],
                    'sender': row['sender'],
                    'amount': parsed['amount'],
                    'merchant': parsed['merchant'],
                    'transaction_type': parsed['transaction_type'],
                    'raw_message': parsed['raw_message'],
                    'category': None,  # To be filled by categorizer
                    'notes': ''
                }
                expenses.append(expense)

        if not expenses:
            return pd.DataFrame()

        df = pd.DataFrame(expenses)

        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])

        return df

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """
        Parse amount string to float

        Args:
            amount_str: String containing amount (may have commas, currency symbols)

        Returns:
            Float amount or None if invalid
        """
        try:
            # Remove commas and currency symbols
            cleaned = re.sub(r'[,\$₹€£¥]', '', amount_str)
            amount = float(cleaned)
            return amount if amount > 0 else None
        except (ValueError, AttributeError):
            return None

    def _clean_merchant_name(self, merchant: str) -> str:
        """
        Clean and normalize merchant name

        Args:
            merchant: Raw merchant name from SMS

        Returns:
            Cleaned merchant name
        """
        if not merchant:
            return 'Unknown'

        # Remove common suffixes/prefixes
        merchant = re.sub(r'\s*\(.*?\)\s*', '', merchant)  # Remove parentheses
        merchant = re.sub(r'\s+on\s+\d{2}.*', '', merchant, re.IGNORECASE)  # Remove date suffixes
        merchant = merchant.strip('.,- ')

        # Capitalize properly
        merchant = merchant.upper()

        # Truncate if too long
        if len(merchant) > 50:
            merchant = merchant[:50]

        return merchant

    def get_parsing_stats(self, original_df: pd.DataFrame, parsed_df: pd.DataFrame) -> Dict:
        """
        Get statistics about parsing success

        Args:
            original_df: Original messages DataFrame
            parsed_df: Parsed expenses DataFrame

        Returns:
            Dictionary with parsing statistics
        """
        return {
            'total_messages': len(original_df),
            'parsed_expenses': len(parsed_df),
            'parsing_rate': len(parsed_df) / len(original_df) if len(original_df) > 0 else 0,
            'total_amount': parsed_df['amount'].sum() if not parsed_df.empty else 0,
            'unique_merchants': parsed_df['merchant'].nunique() if not parsed_df.empty else 0
        }


def main():
    """Test the parser with sample messages"""
    sample_messages = [
        "Your card has been used for Rs 150.50 at STARBUCKS on 15-Jan",
        "You have spent Rs.2,500.00 at AMAZON on 16-Jan-2025",
        "ATM withdrawal of Rs 5000 successful",
        "Transaction of $25.00 at Uber completed",
        "Sent Rs 1000 to John via PayTM",
        "Rs 750 debited from account for SWIGGY",
        "Purchase of Rs.1,200.00 at McDonald's"
    ]

    parser = ExpenseParser()

    print("Testing Expense Parser\n")
    print("=" * 80)

    for msg in sample_messages:
        result = parser.parse_message(msg)
        print(f"\nMessage: {msg}")
        if result:
            print(f"  ✓ Amount: ${result['amount']:.2f}")
            print(f"  ✓ Merchant: {result['merchant']}")
            print(f"  ✓ Type: {result['transaction_type']}")
        else:
            print(f"  ✗ Could not parse")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
