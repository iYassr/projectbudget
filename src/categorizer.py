"""
Categorizer - AI-powered expense categorization
"""
import os
import json
from typing import Dict, List, Optional
import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv


class ExpenseCategorizer:
    """Categorize expenses using AI and rule-based approaches"""

    def __init__(self, config_path: str = "config/categories.json", use_ai: bool = True):
        """
        Initialize categorizer

        Args:
            config_path: Path to categories configuration file
            use_ai: Whether to use AI for categorization (requires API key)
        """
        # Load categories configuration
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.categories = config['categories']
        self.merchant_keywords = config['merchant_keywords']
        self.use_ai = use_ai

        # Initialize Anthropic client if using AI
        self.client = None
        if use_ai:
            load_dotenv()
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.client = Anthropic(api_key=api_key)
            else:
                print("Warning: ANTHROPIC_API_KEY not found. Falling back to rule-based categorization.")
                self.use_ai = False

    def categorize_expense(
        self,
        merchant: str,
        amount: float,
        raw_message: Optional[str] = None,
        learned_category: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Categorize a single expense

        Args:
            merchant: Merchant name
            amount: Transaction amount
            raw_message: Original SMS message
            learned_category: Previously learned category for this merchant

        Returns:
            Dictionary with category and confidence score
        """
        # First check if we have a learned category
        if learned_category:
            return {
                'category': learned_category,
                'confidence': 1.0,
                'method': 'learned'
            }

        # Try rule-based categorization
        rule_category = self._categorize_by_rules(merchant, raw_message)
        if rule_category:
            return {
                'category': rule_category,
                'confidence': 0.8,
                'method': 'rules'
            }

        # Fall back to AI categorization if enabled
        if self.use_ai and self.client:
            ai_category = self._categorize_by_ai(merchant, amount, raw_message)
            if ai_category:
                return {
                    'category': ai_category,
                    'confidence': 0.9,
                    'method': 'ai'
                }

        # Default to 'Other' if nothing else works
        return {
            'category': 'Other',
            'confidence': 0.5,
            'method': 'default'
        }

    def categorize_batch(
        self,
        expenses_df: pd.DataFrame,
        merchant_category_map: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """
        Categorize a batch of expenses

        Args:
            expenses_df: DataFrame with expense data
            merchant_category_map: Dictionary of learned merchant->category mappings

        Returns:
            DataFrame with added category and confidence columns
        """
        if merchant_category_map is None:
            merchant_category_map = {}

        results = []

        for idx, row in expenses_df.iterrows():
            learned = merchant_category_map.get(row['merchant'])

            result = self.categorize_expense(
                merchant=row['merchant'],
                amount=row['amount'],
                raw_message=row.get('raw_message'),
                learned_category=learned
            )

            results.append(result)

        expenses_df['category'] = [r['category'] for r in results]
        expenses_df['category_confidence'] = [r['confidence'] for r in results]
        expenses_df['category_method'] = [r['method'] for r in results]

        return expenses_df

    def _categorize_by_rules(self, merchant: str, raw_message: Optional[str] = None) -> Optional[str]:
        """
        Categorize using keyword matching rules

        Args:
            merchant: Merchant name
            raw_message: Original message

        Returns:
            Category name or None
        """
        search_text = f"{merchant} {raw_message or ''}".lower()

        # Check each category's keywords
        for category, keywords in self.merchant_keywords.items():
            for keyword in keywords:
                if keyword.lower() in search_text:
                    return category

        return None

    def _categorize_by_ai(
        self,
        merchant: str,
        amount: float,
        raw_message: Optional[str] = None
    ) -> Optional[str]:
        """
        Categorize using Claude AI

        Args:
            merchant: Merchant name
            amount: Transaction amount
            raw_message: Original message

        Returns:
            Category name or None
        """
        if not self.client:
            return None

        # Build prompt
        categories_list = "\n".join([f"- {cat}" for cat in self.categories])

        prompt = f"""Categorize this expense into one of the following categories:

{categories_list}

Expense details:
- Merchant: {merchant}
- Amount: ${amount:.2f}
{f"- Original message: {raw_message}" if raw_message else ""}

Respond with ONLY the category name from the list above. Choose the most appropriate category."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=50,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            category = message.content[0].text.strip()

            # Validate category is in our list
            if category in self.categories:
                return category

        except Exception as e:
            print(f"AI categorization error: {e}")

        return None

    def add_category(self, category_name: str, keywords: Optional[List[str]] = None):
        """
        Add a new category

        Args:
            category_name: Name of new category
            keywords: List of keywords for rule-based matching
        """
        if category_name not in self.categories:
            self.categories.append(category_name)

        if keywords:
            if category_name not in self.merchant_keywords:
                self.merchant_keywords[category_name] = []
            self.merchant_keywords[category_name].extend(keywords)

    def get_category_summary(self, expenses_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get summary of expenses by category

        Args:
            expenses_df: DataFrame with categorized expenses

        Returns:
            Summary DataFrame
        """
        if expenses_df.empty or 'category' not in expenses_df.columns:
            return pd.DataFrame()

        summary = expenses_df.groupby('category').agg({
            'amount': ['sum', 'count', 'mean']
        }).round(2)

        summary.columns = ['total_amount', 'count', 'average_amount']
        summary = summary.sort_values('total_amount', ascending=False)

        return summary


def main():
    """Test categorization"""
    categorizer = ExpenseCategorizer(use_ai=False)

    test_expenses = [
        {'merchant': 'STARBUCKS', 'amount': 15.50, 'raw_message': 'Coffee purchase'},
        {'merchant': 'UBER', 'amount': 22.00, 'raw_message': 'Ride payment'},
        {'merchant': 'AMAZON', 'amount': 89.99, 'raw_message': 'Online shopping'},
        {'merchant': 'WHOLE FOODS', 'amount': 125.30, 'raw_message': 'Grocery shopping'},
        {'merchant': 'ATM WITHDRAWAL', 'amount': 100.00, 'raw_message': 'Cash withdrawal'},
    ]

    print("Testing Expense Categorization\n")
    print("=" * 80)

    for expense in test_expenses:
        result = categorizer.categorize_expense(
            merchant=expense['merchant'],
            amount=expense['amount'],
            raw_message=expense['raw_message']
        )

        print(f"\nMerchant: {expense['merchant']}")
        print(f"  Category: {result['category']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Method: {result['method']}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
